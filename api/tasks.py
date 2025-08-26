from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from .models import VerificationCode

@shared_task
def send_verification_email(user_id, email, code):
    """Send verification email with the 6-digit code"""
    subject = 'Verify Your Email Address'
    
    # Create a simple HTML email template
    html_message = f"""
    <html>
    <body>
        <h2>Email Verification</h2>
        <p>Thank you for registering! Please use the following verification code to complete your registration:</p>
        <h1 style="color: #007bff; font-size: 32px; text-align: center; padding: 20px; background-color: #f8f9fa; border-radius: 8px; margin: 20px 0;">
            {code}
        </h1>
        <p>This code will expire in 10 minutes.</p>
        <p>If you didn't request this verification, please ignore this email.</p>
        <hr>
        <p style="color: #6c757d; font-size: 12px;">This is an automated message, please do not reply.</p>
    </body>
    </html>
    """
    
    # Plain text version
    message = f"""
    Email Verification
    
    Thank you for registering! Please use the following verification code to complete your registration:
    
    {code}
    
    This code will expire in 10 minutes.
    
    If you didn't request this verification, please ignore this email.
    """
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Error sending verification email: {e}")
        return False

@shared_task
def cleanup_expired_codes():
    """Clean up expired verification codes"""
    from django.utils import timezone
    expired_codes = VerificationCode.objects.filter(expires_at__lt=timezone.now())
    count = expired_codes.count()
    expired_codes.delete()
    return f"Cleaned up {count} expired verification codes"
