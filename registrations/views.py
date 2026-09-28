from datetime import timedelta
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from loguru import logger

from users.permissions import IsAdminOrSuperUser
from .models import Registration
from .serializers import RegistrationSerializer


class RegistrationViewSet(viewsets.ModelViewSet):
    queryset = Registration.objects.all().order_by('-created_at')
    serializer_class = RegistrationSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['ticket', 'user']
    ordering_fields = ['created_at']

    def get_permissions(self):
        if self.action == 'retrieve':
            return [AllowAny()]
        elif self.action == 'create':
            return [IsAuthenticated()]
        return [IsAdminOrSuperUser()]

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response({'registrations': serializer.data}, status=status.HTTP_200_OK)

    def perform_create(self, serializer):
        registration = serializer.save()
        user_name = registration.user.username if registration.user else 'unknown'
        logger.info(f"Reservation {registration.id} created by {user_name}")

        # Schedule Celery asynchronous email reminder H-2 hours before event start
        try:
            event = registration.ticket.event
            reminder_time = event.start_time - timedelta(hours=2)
            now = timezone.now()

            from .tasks import send_event_reminder_email
            if reminder_time > now:
                send_event_reminder_email.apply_async(
                    args=[str(registration.id)],
                    eta=reminder_time
                )
                logger.info(f"Scheduled event reminder for registration {registration.id} at {reminder_time}")
            else:
                send_event_reminder_email.delay(str(registration.id))
                logger.info(f"Dispatched immediate event reminder for registration {registration.id}")
        except Exception as e:
            logger.warning(f"Could not dispatch reminder email task for registration {registration.id}: {e}")
