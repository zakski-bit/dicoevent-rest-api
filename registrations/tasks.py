from datetime import datetime, timedelta
from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from loguru import logger

@shared_task(bind=True, max_retries=3)
def send_event_reminder_email(self, registration_id: str):
    """
    Celery asynchronous task to send an event reminder email to a registered attendee.
    Dispatched to arrive H-2 hours before the event start time.
    """
    from .models import Registration

    try:
        registration = Registration.objects.select_related('ticket__event', 'user').get(id=registration_id)
        event = registration.ticket.event
        user = registration.user

        if not user.email:
            logger.warning(f"Cannot send reminder: User {user.username} has no email address.")
            return

        subject = f"[Reminder] Event {event.name} Akan Dimulai Segera!"
        formatted_start = event.start_time.strftime('%Y-%m-%d %H:%M')
        message = (
            f"Halo {user.username},\n\n"
            f"Ini adalah pengingat bahwa event '{event.name}' yang telah Anda daftarkan "
            f"akan dimulai dalam 2 jam (pada {formatted_start}).\n\n"
            f"Lokasi: {event.location}\n"
            f"Tiket: {registration.ticket.name}\n\n"
            f"Sampai jumpa di acara!\n\n"
            f"Salam,\nTim DicoEvent"
        )

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )

        logger.info(
            f"Event reminder email sent successfully to {user.email} for registration {registration_id} "
            f"(Event: {event.name})"
        )
    except Registration.DoesNotExist:
        logger.error(f"Registration with ID {registration_id} not found.")
    except Exception as exc:
        logger.error(f"Error sending event reminder email for registration {registration_id}: {exc}")
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60)


@shared_task
def check_and_send_due_event_reminders():
    """
    Periodic task to find registrations for events starting in approximately 2 hours
    and dispatch reminders if not already sent.
    """
    from .models import Registration

    now = timezone.now()
    two_hours_later = now + timedelta(hours=2)
    two_hours_margin = two_hours_later + timedelta(minutes=15)

    due_registrations = Registration.objects.filter(
        ticket__event__start_time__gte=two_hours_later,
        ticket__event__start_time__lte=two_hours_margin
    ).select_related('ticket__event', 'user')

    logger.info(f"Checking due event reminders: found {due_registrations.count()} registrations.")

    for reg in due_registrations:
        send_event_reminder_email.delay(str(reg.id))
