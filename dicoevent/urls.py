from django.contrib import admin
from django.urls import include, re_path
from rest_framework import routers
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from events.views import (
    EventPosterView,
    EventViewSet,
    PosterUploadView,
    ServeMediaView,
)
from payments.views import PaymentViewSet
from registrations.views import RegistrationViewSet
from tickets.views import TicketViewSet
from users.views import AssignRoleView, GroupViewSet, UserViewSet


class OptionalSlashRouter(routers.DefaultRouter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.trailing_slash = '/?'


router = OptionalSlashRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'groups', GroupViewSet, basename='group')
router.register(r'events', EventViewSet, basename='event')
router.register(r'tickets', TicketViewSet, basename='ticket')
router.register(r'registrations', RegistrationViewSet, basename='registration')
router.register(r'payments', PaymentViewSet, basename='payment')

urlpatterns = [
    re_path(r'^admin/?', admin.site.urls),
    re_path(r'^api/login/?$', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    re_path(r'^api/token/?$', TokenRefreshView.as_view(), name='token_refresh'),
    re_path(r'^api/assign-roles/?$', AssignRoleView.as_view(), name='assign_roles'),
    re_path(r'^api/events/upload/?$', PosterUploadView.as_view(), name='event_upload'),
    re_path(r'^api/events/(?P<event_id>[^/]+)/poster/?$', EventPosterView.as_view(), name='event_poster'),
    re_path(r'^api/media/(?P<filename>[^/]+)/?$', ServeMediaView.as_view(), name='serve_media'),
    re_path(r'^api/', include(router.urls)),
]
