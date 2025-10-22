from celery import shared_task
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings

@shared_task
def send_activation_email(user_id, college_id, password_link):
    from users.models import User
    from colleges.models import College

    user = User.objects.get(id=user_id)
    college = College.objects.get(id=college_id)

    subject = f"Set Your Password for {college.name} Portal Access"
    from_email = settings.DEFAULT_FROM_EMAIL
    to_email = [user.email]

    context = {
        "user": user,
        "college": college,
        "password_link": password_link,
        "site_name": "CheckMate Central",
        "support_email": "checkmate.central@gmail.com",
    }

    text_content = render_to_string("colleges/user_activation_link.html", context)
    html_content = render_to_string("colleges/user_activation_link.html", context)

    msg = EmailMultiAlternatives(subject, text_content, from_email, to_email)
    msg.attach_alternative(html_content, "text/html")
    msg.send()