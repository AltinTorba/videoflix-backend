from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from .functions import (
    build_activation_link,
    build_password_reset_link,
    set_auth_cookies,
    delete_auth_cookies,
)
from .serializers import (
    RegistrationSerializer,
    LoginSerializer,
    PasswordResetRequestSerializer,
    PasswordConfirmSerializer,
)
from .tasks import send_activation_email_task, send_password_reset_email_task

User = get_user_model()

GENERIC_ERROR = {"detail": "Bitte ueberpruefe deine Eingaben und versuche es erneut."}


class RegisterView(APIView):
    """Registers a new, initially inactive user."""

    permission_classes = [AllowAny]

    def post(self, request):
        """Create the user and send the activation email.

        Args:
            request: Contains email, password, confirmed_password.

        Returns:
            Response: 201 with user data on success, otherwise 400 with a
            generic error message (for security reasons).
        """
        serializer = RegistrationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(GENERIC_ERROR, status=400)
        user = serializer.save()
        link = build_activation_link(user)
        send_activation_email_task.delay(user.email, link)
        return Response({"user": {"id": user.id, "email": user.email}}, status=201)


class ActivateView(APIView):
    """Activates a user account using uidb64 and a token."""

    permission_classes = [AllowAny]

    def get(self, request, uidb64, token):
        """Verify the activation link and activate the user.

        Args:
            request: The incoming HTTP request.
            uidb64: Base64-encoded user id from the email link.
            token: Activation token from the email link.

        Returns:
            Response: 200 on successful activation, otherwise 400.
        """
        user = self._get_user_from_uid(uidb64)
        if user is None or not default_token_generator.check_token(user, token):
            return Response({"detail": "Aktivierung fehlgeschlagen."}, status=400)
        user.is_active = True
        user.save()
        return Response({"message": "Account successfully activated."}, status=200)

    def _get_user_from_uid(self, uidb64):
        """Decode uidb64 and load the matching user.

        Args:
            uidb64: Base64-encoded user id.

        Returns:
            User | None: The user, or None if invalid/not found.
        """
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            return User.objects.get(pk=uid)
        except (User.DoesNotExist, ValueError, TypeError, OverflowError):
            return None


class LoginView(APIView):
    """Authenticates a user and sets JWT cookies."""

    permission_classes = [AllowAny]

    def post(self, request):
        """Verify login credentials and set auth cookies on success.

        Args:
            request: Contains email and password.

        Returns:
            Response: 200 with cookies set on success, otherwise 400.
        """
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = self._authenticate(serializer.validated_data)
        if user is None:
            return Response(GENERIC_ERROR, status=400)
        return self._build_login_response(user)

    def _authenticate(self, data):
        """Check email, password, and activation status of the user.

        Args:
            data: Validated data containing email and password.

        Returns:
            User | None: The user if credentials are valid, otherwise None.
        """
        try:
            user = User.objects.get(email=data["email"])
        except User.DoesNotExist:
            return None
        if not user.is_active or not user.check_password(data["password"]):
            return None
        return user

    def _build_login_response(self, user):
        """Issue new JWT tokens and attach them as cookies.

        Args:
            user: The successfully authenticated user.

        Returns:
            Response: 200 with user data and auth cookies set.
        """
        refresh = RefreshToken.for_user(user)
        body = {"detail": "Login successful", "user": {"id": user.id, "username": user.email}}
        response = Response(body, status=200)
        return set_auth_cookies(response, refresh.access_token, refresh)


class LogoutView(APIView):
    """Logs the user out and invalidates the refresh token."""

    def post(self, request):
        """Blacklist the refresh token and delete auth cookies.

        Args:
            request: Must contain the refresh_token cookie.

        Returns:
            Response: 200 on success, otherwise 400 if the token is missing.
        """
        refresh_token = request.COOKIES.get("refresh_token")
        if refresh_token is None:
            return Response({"detail": "Refresh-Token fehlt."}, status=400)
        self._blacklist_token(refresh_token)
        body = {"detail": "Logout successful! All tokens will be deleted."}
        response = Response(body, status=200)
        return delete_auth_cookies(response)

    def _blacklist_token(self, refresh_token):
        """Blacklist the refresh token, ignoring invalid tokens.

        Args:
            refresh_token: The refresh token to invalidate.
        """
        try:
            RefreshToken(refresh_token).blacklist()
        except TokenError:
            pass


class CookieTokenRefreshView(APIView):
    """Refreshes the access token using the refresh token cookie."""

    permission_classes = [AllowAny]

    def post(self, request):
        """Read the refresh_token cookie and issue a new access token.

        Args:
            request: Must contain the refresh_token cookie.

        Returns:
            Response: 200 with a new access token, otherwise 400/401.
        """
        refresh_token = request.COOKIES.get("refresh_token")
        if refresh_token is None:
            return Response({"detail": "Refresh-Token fehlt."}, status=400)
        return self._refresh(refresh_token)

    def _refresh(self, refresh_token):
        """Validate the refresh token and set a new access token cookie.

        Args:
            refresh_token: The refresh token sent by the client.

        Returns:
            Response: 200 with a new access_token cookie, otherwise 401.
        """
        try:
            refresh = RefreshToken(refresh_token)
        except TokenError:
            return Response({"detail": "Ungueltiger Refresh-Token."}, status=401)
        body = {"detail": "Token refreshed", "access": str(refresh.access_token)}
        response = Response(body, status=200)
        response.set_cookie(
            "access_token", str(refresh.access_token), httponly=True, samesite="Lax"
        )
        return response


class PasswordResetRequestView(APIView):
    """Accepts password reset requests and sends the reset email."""

    permission_classes = [AllowAny]

    def post(self, request):
        """Send a reset email if an account with this address exists.

        Args:
            request: Contains the email address.

        Returns:
            Response: 200 with a generic confirmation (regardless of
            whether the account actually exists, for security reasons).
        """
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self._trigger_reset_email(serializer.validated_data["email"])
        return Response({"detail": "An email has been sent to reset your password."}, status=200)

    def _trigger_reset_email(self, email):
        """Look up the user and send the reset email if found.

        Args:
            email: The requested email address.
        """
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return
        link = build_password_reset_link(user)
        send_password_reset_email_task.delay(user.email, link)


class PasswordConfirmView(APIView):
    """Sets a new password using uidb64 and a token."""

    permission_classes = [AllowAny]

    def post(self, request, uidb64, token):
        """Verify the reset link and store the new password.

        Args:
            request: Contains new_password and confirm_password.
            uidb64: Base64-encoded user id from the email link.
            token: Reset token from the email link.

        Returns:
            Response: 200 on success, otherwise 400 for an invalid link.
        """
        serializer = PasswordConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = self._get_valid_user(uidb64, token)
        if user is None:
            return Response({"detail": "Ungueltiger oder abgelaufener Link."}, status=400)
        user.set_password(serializer.validated_data["new_password"])
        user.save()
        return Response({"detail": "Your Password has been successfully reset."}, status=200)

    def _get_valid_user(self, uidb64, token):
        """Decode uidb64 and validate the token against the user.

        Args:
            uidb64: Base64-encoded user id.
            token: Reset token to validate.

        Returns:
            User | None: The user if the token is valid, otherwise None.
        """
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (User.DoesNotExist, ValueError, TypeError, OverflowError):
            return None
        return user if default_token_generator.check_token(user, token) else None
