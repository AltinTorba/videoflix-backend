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

GENERIC_ERROR = {"detail": "Bitte überprüfe deine Eingaben und versuche es erneut."}


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(GENERIC_ERROR, status=400)
        user = serializer.save()
        link = build_activation_link(user)
        send_activation_email_task.delay(user.email, link)
        return Response({"user": {"id": user.id, "email": user.email}}, status=201)


class ActivateView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, uidb64, token):
        user = self._get_user_from_uid(uidb64)
        if user is None or not default_token_generator.check_token(user, token):
            return Response({"detail": "Aktivierung fehlgeschlagen."}, status=400)
        user.is_active = True
        user.save()
        return Response({"message": "Account successfully activated."}, status=200)

    def _get_user_from_uid(self, uidb64):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            return User.objects.get(pk=uid)
        except (User.DoesNotExist, ValueError, TypeError, OverflowError):
            return None


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = self._authenticate(serializer.validated_data)
        if user is None:
            return Response(GENERIC_ERROR, status=400)
        return self._build_login_response(user)

    def _authenticate(self, data):
        try:
            user = User.objects.get(email=data["email"])
        except User.DoesNotExist:
            return None
        if not user.is_active or not user.check_password(data["password"]):
            return None
        return user

    def _build_login_response(self, user):
        refresh = RefreshToken.for_user(user)
        body = {"detail": "Login successful", "user": {"id": user.id, "username": user.email}}
        response = Response(body, status=200)
        return set_auth_cookies(response, refresh.access_token, refresh)


class LogoutView(APIView):
    def post(self, request):
        refresh_token = request.COOKIES.get("refresh_token")
        if refresh_token is None:
            return Response({"detail": "Refresh-Token fehlt."}, status=400)
        self._blacklist_token(refresh_token)
        body = {"detail": "Logout successful! All tokens will be deleted."}
        response = Response(body, status=200)
        return delete_auth_cookies(response)

    def _blacklist_token(self, refresh_token):
        try:
            RefreshToken(refresh_token).blacklist()
        except TokenError:
            pass


class CookieTokenRefreshView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = request.COOKIES.get("refresh_token")
        if refresh_token is None:
            return Response({"detail": "Refresh-Token fehlt."}, status=400)
        return self._refresh(refresh_token)

    def _refresh(self, refresh_token):
        try:
            refresh = RefreshToken(refresh_token)
        except TokenError:
            return Response({"detail": "Ungültiger Refresh-Token."}, status=401)
        body = {"detail": "Token refreshed", "access": str(refresh.access_token)}
        response = Response(body, status=200)
        response.set_cookie(
            "access_token", str(refresh.access_token), httponly=True, samesite="Lax"
        )
        return response


class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self._trigger_reset_email(serializer.validated_data["email"])
        return Response({"detail": "An email has been sent to reset your password."}, status=200)

    def _trigger_reset_email(self, email):
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return
        link = build_password_reset_link(user)
        send_password_reset_email_task.delay(user.email, link)


class PasswordConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, uidb64, token):
        serializer = PasswordConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = self._get_valid_user(uidb64, token)
        if user is None:
            return Response({"detail": "Ungültiger oder abgelaufener Link."}, status=400)
        user.set_password(serializer.validated_data["new_password"])
        user.save()
        return Response({"detail": "Your Password has been successfully reset."}, status=200)

    def _get_valid_user(self, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (User.DoesNotExist, ValueError, TypeError, OverflowError):
            return None
        return user if default_token_generator.check_token(user, token) else None
