from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode


def build_activation_link(user):
    """Build the activation link included in the confirmation email.

    Args:
        user: The newly registered user.

    Returns:
        str: Full frontend URL containing uid and activation token.
    """
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    return f"{settings.FRONTEND_URL}/pages/auth/activate.html?uid={uidb64}&token={token}"


def build_password_reset_link(user):
    """Build the link included in the password reset email.

    Args:
        user: The user whose password should be reset.

    Returns:
        str: Full frontend URL containing uid and reset token.
    """
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    return f"{settings.FRONTEND_URL}/pages/auth/confirm_password.html?uid={uidb64}&token={token}"


def set_auth_cookies(response, access_token, refresh_token):
    """Set access and refresh tokens as HttpOnly cookies on the response.

    Args:
        response: The response object the cookies are set on.
        access_token: The JWT access token.
        refresh_token: The JWT refresh token.

    Returns:
        Response: The response with the auth cookies set.
    """
    cookie_kwargs = {
        "httponly": True,
        "secure": settings.AUTH_COOKIE_SECURE,
        "samesite": settings.AUTH_COOKIE_SAMESITE,
    }
    response.set_cookie(settings.AUTH_COOKIE_ACCESS, str(access_token), **cookie_kwargs)
    response.set_cookie(settings.AUTH_COOKIE_REFRESH, str(refresh_token), **cookie_kwargs)
    return response


def delete_auth_cookies(response):
    """Delete access and refresh token cookies (used on logout).

    Args:
        response: The response object the cookies are removed from.

    Returns:
        Response: The response without auth cookies.
    """
    response.delete_cookie(settings.AUTH_COOKIE_ACCESS)
    response.delete_cookie(settings.AUTH_COOKIE_REFRESH)
    return response
