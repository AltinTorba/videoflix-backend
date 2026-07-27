from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode


def build_activation_link(user):
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    return f"{settings.FRONTEND_URL}/activate/{uidb64}/{token}/"


def build_password_reset_link(user):
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    return f"{settings.FRONTEND_URL}/reset-password/{uidb64}/{token}/"


def set_auth_cookies(response, access_token, refresh_token):
    cookie_kwargs = {
        "httponly": True,
        "secure": settings.AUTH_COOKIE_SECURE,
        "samesite": settings.AUTH_COOKIE_SAMESITE,
    }
    response.set_cookie(settings.AUTH_COOKIE_ACCESS, str(access_token), **cookie_kwargs)
    response.set_cookie(settings.AUTH_COOKIE_REFRESH, str(refresh_token), **cookie_kwargs)
    return response


def delete_auth_cookies(response):
    response.delete_cookie(settings.AUTH_COOKIE_ACCESS)
    response.delete_cookie(settings.AUTH_COOKIE_REFRESH)
    return response
