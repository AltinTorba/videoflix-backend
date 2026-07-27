from django.core.mail import send_mail
from django.conf import settings
from django_rq import job


@job
def send_activation_email_task(email, activation_link):
    subject = "Aktiviere dein Videoflix-Konto"
    message = f"Bitte aktiviere dein Konto über folgenden Link: {activation_link}"
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])


@job
def send_password_reset_email_task(email, reset_link):
    subject = "Videoflix Passwort zurücksetzen"
    message = f"Setze dein Passwort über folgenden Link zurück: {reset_link}"
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])
