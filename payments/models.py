import uuid
from decimal import Decimal

from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator


User = get_user_model()


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Payment(TimeStampedModel):
    class PaymentStatus(models.TextChoices):
        PENDING = 'pending', 'Очікує на оплату'
        PROCESSING = 'processing', 'Обробляється'
        SUCCEEDED = 'succeeded', 'Успішно'
        FAILED = 'failed', 'Не вдалося'
        CANCELLED = 'cancelled', 'Скасовано'
        REFUNDED = 'refunded', 'Повернено'
        PARTIALLY_REFUNDED = 'partially_refunded', 'Частково повернено'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name='payments')
    stripe_payment_intent_id = models.CharField(max_length=255, unique=True, db_index=True)
    stripe_charge_id = models.CharField(max_length=255, unique=True, db_index=True, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.50'))])
    currency = models.CharField(max_length=5, default='USD')
    status = models.CharField(max_length=30, choices=PaymentStatus.choices, default=PaymentStatus.PENDING)
    description = models.TextField(blank=True, null=True)
    metadata = models.JSONField(blank=True, null=True, default=dict)
    error_message = models.TextField(blank=True, null=True)
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

    class Meta:
        db_table = 'stripe_payments'
        verbose_name = 'Платіж'
        verbose_name_plural = 'Платежі'
        ordering = ['-created_at']

    def __str__(self):
        return f'Payment {self.id} - {self.amount} {self.currency} ({self.status})'

    @property
    def is_successful(self):
        return self.status == self.PaymentStatus.SUCCEEDED

    @property
    def can_be_refunded(self):
        return self.status == self.PaymentStatus.SUCCEEDED and self.refund_amount <= self.amount
