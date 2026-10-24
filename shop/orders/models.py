from django.db import models
from django.utils.translation import gettext_lazy as _

from shop.models import Product, Customer


class Order(models.Model):
    class OrderStatus(models.TextChoices):
        PENDING = 'pending', _('Очікує')
        PAID = 'paid', _('Оплачено')
        CREATED = 'created', _('Створено')
        DELIVERED = 'delivered', _('Доставлено')
        CANCELLED = 'cancelled', _('Скасовано')

    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, null=True, blank=True, related_name='order')
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField()
    phone = models.CharField(max_length=10)
    address = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=OrderStatus.choices, default=OrderStatus.CREATED)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment = models.OneToOneField(
        'payments.Payment',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='order'
    )

    class Meta:
        verbose_name = _('Замовлення')
        verbose_name_plural = _('Замовлення')
        ordering = ['-created_at']

    def __str__(self):
        return f'Замовлення {self.id} - {self.first_name} {self.last_name}'


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = _('Елемент замовлення')
        verbose_name_plural = _('Елементи замовлення')

    def __str__(self):
        return f'{self.quantity} x {self.product.name} - {self.price} (Замовлення {self.order.id})'

    def save(self, *args, **kwargs):
        self.price = self.product.current_price
        super().save(*args, **kwargs)

    def get_total_price(self):
        return self.price * self.quantity
