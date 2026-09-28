from django.contrib.auth import get_user_model
from rest_framework import serializers
from tickets.models import Ticket
from .models import Registration

User = get_user_model()


class RegistrationSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)
    ticket_id = serializers.UUIDField(write_only=True)
    user_id = serializers.UUIDField(write_only=True)
    ticket = serializers.SerializerMethodField(read_only=True)
    user = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Registration
        fields = [
            'id',
            'ticket',
            'user',
            'ticket_id',
            'user_id',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_ticket(self, obj):
        return str(obj.ticket_id)

    def get_user(self, obj):
        return str(obj.user_id)

    def create(self, validated_data):
        ticket_id = validated_data.pop('ticket_id')
        user_id = validated_data.pop('user_id')
        ticket = Ticket.objects.get(id=ticket_id)
        user = User.objects.get(id=user_id)
        registration = Registration.objects.create(ticket=ticket, user=user, **validated_data)
        return registration

    def update(self, instance, validated_data):
        ticket_id = validated_data.pop('ticket_id', None)
        user_id = validated_data.pop('user_id', None)
        if ticket_id:
            instance.ticket = Ticket.objects.get(id=ticket_id)
        if user_id:
            instance.user = User.objects.get(id=user_id)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
