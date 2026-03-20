from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template, render_to_string
from django.conf import settings
from config.env_config import ENV
from users.models import User
from audit.models import Notifications
from celery import shared_task


@shared_task
def send_email_task(subject: str, to_email: str, html_content: str, plain_text: str):
    """
    Async email sending task — queued to Celery worker.
    All emails go through here so none of them block the request.
    """
    try:
        email = EmailMultiAlternatives(
            from_email=ENV.EMAIL_HOST_USER,
            to=[to_email],
            subject=subject,
            body=plain_text,
        )
        email.attach_alternative(html_content, "text/html")
        email.send(fail_silently=False)
    except Exception as ex:
        raise Exception(f"Failed to send email to {to_email}: {str(ex)}")


class EmailService:

    @staticmethod
    def _send(subject: str, to_email: str, html_content: str, plain_text: str) -> None:
        # queue to Celery — returns immediately, worker handles sending
        send_email_task.delay(
            subject=subject,
            to_email=to_email,
            html_content=html_content,
            plain_text=plain_text,
        )

    @classmethod
    def send_otp(cls, user: User, otp_code: str) -> None:
        """
          Sends a password reset OTP to the user's email.

        Args:
            user (User): The user requesting the password reset.
            otp_code (str): The generated 6 digit OTP code.

        Raises:
            Exception: If rendering or sending fails.
        """
        try:
            # render the HTML template with context
            html_content = render_to_string(
                "otp_email.html",  # ← just the filename since APP_DIRS=True
                #   Django will find it inside services/otp_email/templates/
                {
                    "fullname": user.first_name + " " + user.last_name,
                    "otp_code": otp_code,
                },
            )

            # plain text fallback for email clients that don't render HTML
            plain_text = (
                f"Hello {user.first_name},\n\n"
                f"Your OTP code is: {otp_code}\n\n"
                f"This code expires in 15 minutes.\n\n"
                f"If you did not request this, please ignore this email."
            )

            cls._send(
                subject="Your Password Reset OTP Code",
                to_email=user.email,
                html_content=html_content,
                plain_text=plain_text,
            )
        except Exception as ex:
            raise Exception(f"failed to send OTP email to {user.email}: {str(ex)}")

    @classmethod
    def send_notification(cls, user: User, notification: Notifications):
        """
        Sends an in-app notification as an email to the user.
        Called from NotificationService.notify() when channel is EMAIL.

        Args:
            user (User): The recipient.
            notification: The Notifications model instance.

        Raises:
            Exception: If rendering or sending fails.

        """
        try:

            html_content = render_to_string(
                "notification_email.html",
                {
                    "fullname": user.first_name + " " + user.last_name,
                    "event_name": notification.transaction_log.event_type.name,
                    "message": notification.transaction_log.event_message,
                    "triggered_by": (
                        notification.transaction_log.triggered_by.email
                        if notification.transaction_log.triggered_by
                        else "System"
                    ),
                },
            )

            plain_text = (
                f"Hello {user.first_name},\n\n"
                f"You have a new notification {notification.transaction_log.event_type.name}\n\n"
                f"{notification.transaction_log.event_message}\n\n"
                f"Triggered by {notification.transaction_log.triggered_by.email if notification.transaction_log.triggered_by else 'System'}"
            )

            cls._send(
                subject=f"Notification: {notification.transaction_log.event_type.name}",
                to_email=user.email,
                html_content=html_content,
                plain_text=plain_text,
            )

        except Exception as ex:
            raise Exception(
                f"Failed to send notification email to {user.email}: {str(ex)}"
            )
