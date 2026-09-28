from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import Event, EventPoster

User = get_user_model()


class EventSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)
    organizer_id = serializers.UUIDField(write_only=True, required=False)
    start_time = serializers.DateTimeField(format='%Y-%m-%d %H:%M', input_formats=['%Y-%m-%d %H:%M', '%Y-%m-%d %H:%M:%S', 'iso-8601'])
    end_time = serializers.DateTimeField(format='%Y-%m-%d %H:%M', input_formats=['%Y-%m-%d %H:%M', '%Y-%m-%d %H:%M:%S', 'iso-8601'])

    class Meta:
        model = Event
        fields = [
            'id',
            'name',
            'description',
            'location',
            'start_time',
            'end_time',
            'status',
            'category',
            'quota',
            'organizer_id',
        ]

    def create(self, validated_data):
        organizer_id = validated_data.pop('organizer_id', None)
        request = self.context.get('request')
        if organizer_id:
            organizer = User.objects.get(id=organizer_id)
        elif request and request.user.is_authenticated:
            organizer = request.user
        else:
            raise serializers.ValidationError({'organizer_id': 'Organizer is required.'})

        event = Event.objects.create(organizer=organizer, **validated_data)
        return event

    def update(self, instance, validated_data):
        organizer_id = validated_data.pop('organizer_id', None)
        if organizer_id:
            instance.organizer = User.objects.get(id=organizer_id)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class EventPosterSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)
    event = serializers.PrimaryKeyRelatedField(read_only=True)
    image = serializers.CharField(read_only=True)

    class Meta:
        model = EventPoster
        fields = ['id', 'image', 'event', 'created_at']

