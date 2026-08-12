from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django_rq import job


@job
def send_activation_email_task(email, activation_link):
    subject = "Confirm your email"
    text_body = f"Bitte aktiviere dein Konto über folgenden Link: {activation_link}"
    html_body = render_to_string(
        "emails/activation_email.html",
        {"email": email, "activation_link": activation_link},
    )
    send_html_email(subject, text_body, html_body, email)


@job
def send_password_reset_email_task(email, reset_link):
    subject = "Reset your Password"
    text_body = f"Setze dein Passwort über folgenden Link zurück: {reset_link}"
    html_body = render_to_string(
        "emails/password_reset_email.html", {"reset_link": reset_link}
    )
    send_html_email(subject, text_body, html_body, email)


def send_html_email(subject, text_body, html_body, recipient_email):
    message = EmailMultiAlternatives(
        subject, text_body, settings.DEFAULT_FROM_EMAIL, [recipient_email]
    )
    message.attach_alternative(html_body, "text/html")
    message.send()
