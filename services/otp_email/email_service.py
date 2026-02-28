from django.core.mail import  EmailMultiAlternatives
from django.template.loader import get_template, render_to_string
from django.conf import settings
from config.env_config import ENV
from users.models import User

class EmailService:
    @staticmethod
    def send_otp(user: User, otp_code: str) -> None:
        """
         Sends the OTP code to the user's email using the HTML template.
        Falls back to plain text if HTML rendering fails.

        Args:
            user (User): The user to send the OTP to.
            otp_code (str): The generated OTP code.

        Raises:
            Exception: If email sending fails.
        :param user:
        :param otp_code:
        :return:
        """
        try:
            subject = "Your Password Reset OTP code"
            from_email = ENV.EMAIL_HOST_USER
            to_email = user.email

            # render the HTML template with context
            html_content = render_to_string(
                'otp_email.html', # ← just the filename since APP_DIRS=True
                #   Django will find it inside services/otp_email/templates/

                {
                    'fullname': user.first_name + ' '+ user.last_name,
                    'otp_code': otp_code
                }
            )

            # plain text fallback for email clients that don't render HTML

            plain_text = (
                f"Hello {user.first_name},\n\n"
                f"Your OTP code is: {otp_code}\n\n"
                f"This code expires in 15 minutes.\n\n"
                f"If you did not request this, please ignore this email."
            )

            # Initialize a single email message (which can be sent to multiple recipients).
            email = EmailMultiAlternatives(
                subject=subject,
                body=plain_text,
                from_email=from_email,
                to_email=[to_email]
            )

            # Attach an alternative content representation.
            email.attach_alternative(html_content,'text/html')
            email.send(fail_silently=False)

        except Exception as ex:
            raise Exception(f"failed to send OTP email to {user.email}: {str(ex)}")