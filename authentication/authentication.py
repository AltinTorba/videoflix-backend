from django.conf import settings
from rest_framework_simplejwt.authentication import JWTAuthentication


class CookieJWTAuthentication(JWTAuthentication):
    """Reads the JWT access token from the HttpOnly cookie instead of the header."""

    def authenticate(self, request):
        """Validate the access_token cookie and return (user, token).

        Args:
            request: The incoming HTTP request.

        Returns:
            tuple[User, Token] | None: The authenticated user and the
            validated token, or None if no cookie is present.
        """
        raw_token = request.COOKIES.get(settings.AUTH_COOKIE_ACCESS)
        if raw_token is None:
            return None
        validated_token = self.get_validated_token(raw_token)
        return self.get_user(validated_token), validated_token
