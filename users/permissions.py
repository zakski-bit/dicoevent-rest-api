from rest_framework import permissions


class IsSuperUser(permissions.BasePermission):
    """
    Allows access only to superusers.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_superuser)


class IsAdminOrSuperUser(permissions.BasePermission):
    """
    Allows access to superusers or users in the 'admin' group.
    """
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.user.is_superuser:
            return True
        return request.user.groups.filter(name__iexact='admin').exists()


class IsOrganizerOrAdminOrSuperUser(permissions.BasePermission):
    """
    Allows access to superusers, admins, or organizers.
    """
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.user.is_superuser:
            return True
        return request.user.groups.filter(name__in=['admin', 'organizer']).exists()


class IsEventOrganizerOrAdminOrSuperUser(permissions.BasePermission):
    """
    Object-level permission:
    - Superusers and admins can edit/delete any event.
    - Organizers can only edit/delete their own event.
    """
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.user.is_superuser:
            return True
        return request.user.groups.filter(name__in=['admin', 'organizer']).exists()

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.user.is_superuser:
            return True
        if request.user.groups.filter(name__iexact='admin').exists():
            return True
        # Check if user is organizer and owner of the event
        if request.user.groups.filter(name__iexact='organizer').exists():
            return str(obj.organizer_id) == str(request.user.id)
        return False
