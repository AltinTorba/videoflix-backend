from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django_rq import job


@job
def send_activation_email_task(email, activation_link):
    """Django RQ job: sends the activation email in the background.

    Args:
        email: Recipient email address.
        activation_link: Full activation link.
    """
    subject = "Confirm your email"
    text_body = f"Please activate your account using the following link: {activation_link}"
    html_body = render_to_string(
        "emails/activation_email.html",
        {"email": email, "activation_link": activation_link},
    )
    send_html_email(subject, text_body, html_body, email)


@job
def send_password_reset_email_task(email, reset_link):
    """Django RQ job: sends the password reset email in the background.

    Args:
        email: Recipient email address.
        reset_link: Full password reset link.
    """
    subject = "Reset your Password"
    text_body = f"Reset your password using the following link: {reset_link}"
    html_body = render_to_string(
        "emails/password_reset_email.html", {"reset_link": reset_link}
    )
    send_html_email(subject, text_body, html_body, email)


def send_html_email(subject, text_body, html_body, recipient_email):
    """Build and send an email with a plain-text and an HTML alternative.

    Args:
        subject: Email subject line.
        text_body: Plain-text fallback for clients without HTML support.
        html_body: Rendered HTML content of the email.
        recipient_email: Recipient email address.
    """
    message = EmailMultiAlternatives(
        subject, text_body, settings.DEFAULT_FROM_EMAIL, [recipient_email]
    )
    message.attach_alternative(html_body, "text/html")
    message.send()
