from decimal import Decimal

from rest_framework import serializers

from payments.models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    can_be_refunded = serializers.BooleanField(read_only=True)
    remaining_amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        source='amount',
        read_only=True
    )

    class Meta:
        model = Payment
        fields = '__all__'
        read_only_fields = [
            'id',
            'stripe_payment_intent_id',
            'stripe_charge_id',
            'status',
            'refund_amount',
            'created_at',
            'updated_at'
        ]


class CreatePaymentSerializer(serializers.Serializer):
    amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal('0.50'),
        help_text="Мінімальна сума платежу повинна бути не менше 0.50"
    )
    currency = serializers.ChoiceField(
        choices=['usd', 'eur', 'uah',],
        default='usd',
        help_text='Валюта платежу. Підтримувані значення: usd, eur, uah'
    )
    description = serializers.CharField(
        max_length=500,
        required=False,
        allow_blank=True,
        help_text='Опис платежу (необов\'язково)'
    )
    metadata = serializers.JSONField(
        required=False,
        default=dict,
        help_text='Додаткові дані у форматі JSON (необов\'язково)'
    )
