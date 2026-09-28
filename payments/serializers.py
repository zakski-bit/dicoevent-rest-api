from rest_framework import serializers
from registrations.models import Registration
from .models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)
    registration_id = serializers.UUIDField(write_only=True)
    registration = serializers.SerializerMethodField(read_only=True)
    payment_status = serializers.CharField()

    class Meta:
        model = Payment
        fields = [
            'id',
            'registration',
            'registration_id',
            'payment_method',
            'payment_status',
            'amount_paid',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_registration(self, obj):
        return str(obj.registration_id)

    def validate_payment_status(self, value):
        # Format "completed" as "Completed" to match Postman expectations
        if value.lower() == 'completed':
            return 'Completed'
        elif value.lower() == 'pending':
            return 'Pending'
        return value.capitalize()

    def create(self, validated_data):
        registration_id = validated_data.pop('registration_id')
        registration = Registration.objects.get(id=registration_id)
        payment = Payment.objects.create(registration=registration, **validated_data)
        return payment

    def update(self, instance, validated_data):
        registration_id = validated_data.pop('registration_id', None)
        if registration_id:
            instance.registration = Registration.objects.get(id=registration_id)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
