# signals.py
from django.dispatch import Signal, receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import DeleteRequest

# Define a custom signal
delete_request_created = Signal()

@receiver(delete_request_created)
def send_delete_request_notification(sender, **kwargs):
    delete_request = kwargs['delete_request']
    admin_email = settings.ADMIN_EMAIL  # Ensure you have this setting in your settings.py

    subject = "Delete Confirmation Requested for Student"
    message = (f"A delete confirmation has been requested for student "
               f"{delete_request.student.user} by {delete_request.requested_by}.\n"
               f"Please review and confirm the deletion.")
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [admin_email])
