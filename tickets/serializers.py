from rest_framework import serializers
from events.models import Event
from .models import Ticket


class TicketSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)
    event_id = serializers.UUIDField(write_only=True)
    event = serializers.SerializerMethodField(read_only=True)
    sales_start = serializers.DateTimeField(format='%Y-%m-%d %H:%M', input_formats=['%Y-%m-%d %H:%M', '%Y-%m-%d %H:%M:%S', 'iso-8601'])
    sales_end = serializers.DateTimeField(format='%Y-%m-%d %H:%M', input_formats=['%Y-%m-%d %H:%M', '%Y-%m-%d %H:%M:%S', 'iso-8601'])

    class Meta:
        model = Ticket
        fields = [
            'id',
            'event',
            'event_id',
            'name',
            'price',
            'sales_start',
            'sales_end',
            'quota',
        ]

    def get_event(self, obj):
        return str(obj.event_id)

    def create(self, validated_data):
        event_id = validated_data.pop('event_id')
        event = Event.objects.get(id=event_id)
        ticket = Ticket.objects.create(event=event, **validated_data)
        return ticket

    def update(self, instance, validated_data):
        event_id = validated_data.pop('event_id', None)
        if event_id:
            instance.event = Event.objects.get(id=event_id)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
