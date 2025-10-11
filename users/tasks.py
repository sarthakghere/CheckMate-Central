# users/tasks.py
from celery import shared_task
from django.core.mail import send_mail
import os

@shared_task
def send_login_otp(email, otp):
    subject = 'Your Login OTP'
    message = f'Your OTP is {otp}'
    send_mail(subject=subject, message=message, from_email=os.getenv('EMAIL_HOST_USER'), recipient_list=[email])
