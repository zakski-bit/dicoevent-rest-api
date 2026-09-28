from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .permissions import IsAdminOrSuperUser, IsSuperUser
from .serializers import AssignRoleSerializer, GroupSerializer, UserSerializer

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('username')
    serializer_class = UserSerializer

    def get_permissions(self):
        if self.action in ['create', 'retrieve']:
            return [AllowAny()]
        elif self.action in ['list', 'destroy']:
            return [IsAdminOrSuperUser()]
        return [IsAuthenticated()]

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response({'users': serializer.data}, status=status.HTTP_200_OK)

    def update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return super().update(request, *args, **kwargs)


class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all().order_by('id')
    serializer_class = GroupSerializer

    def get_permissions(self):
        if self.action == 'retrieve':
            return [AllowAny()]
        return [IsSuperUser()]

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response({'groups': serializer.data}, status=status.HTTP_200_OK)


class AssignRoleView(APIView):
    permission_classes = [IsSuperUser]

    def post(self, request, *args, **kwargs):
        serializer = AssignRoleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_id = serializer.validated_data['user_id']
        group_id = serializer.validated_data['group_id']

        user = get_object_or_404(User, id=user_id)
        group = get_object_or_404(Group, id=group_id)

        user.groups.add(group)
        return Response(
            {
                'message': f"User '{user.username}' successfully assigned to role '{group.name}'."
            },
            status=status.HTTP_201_CREATED
        )
