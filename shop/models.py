from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from mptt.models import MPTTModel, TreeForeignKey


User = get_user_model()


class Category(MPTTModel):
    name = models.CharField(_('Назва категорії'), max_length=255)
    slug = models.SlugField(_('Слаг категорії'), max_length=255, unique=True)
    parent = TreeForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    is_active = models.BooleanField(_('Активна'), default=True)

    class MPTTMeta:
        order_insertion_by = ['name']

    class Meta:
        verbose_name = _('Категорія')
        verbose_name_plural = _('Категорії')

    def __str__(self):
        return self.name


class ActiveProductManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True, stock__gt=0)


class Product(models.Model):
    name = models.CharField(_('Назва товару'), max_length=255)
    slug = models.SlugField(_('Слаг товару'), max_length=255, unique=True)
    description = models.TextField(_('Опис товару'), blank=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='product')
    price = models.DecimalField(_('Ціна'), max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(_('Ціна зі знижкою'), max_digits=10, decimal_places=2, null=True, blank=True)
    stock = models.PositiveIntegerField(_('Кількість на складі'), default=0)
    is_active = models.BooleanField(_('Активний'), default=True)
    created_at = models.DateTimeField(_('Дата створення'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Дата оновлення'), auto_now=True)

    objects = models.Manager()
    active = ActiveProductManager()

    class Meta:
        verbose_name = _('Товар')
        verbose_name_plural = _('Товари')
        ordering = ['-created_at']
        constraints = [
            models.CheckConstraint(condition=models.Q(price__gte=0), name='non_negative_price'),
            models.CheckConstraint(condition=models.Q(discount_price__gte=0), name='non_negative_discount_price'),
            models.CheckConstraint(condition=models.Q(stock__gte=0), name='non_negative_stock'),
        ]

    def __str__(self):
        return f'{self.name} - {self.price}'

    @property
    def current_price(self):
        return self.discount_price or self.price


class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='customer_profile')
    phone = models.CharField(_('Номер телефону'), max_length=10, blank=True)
    address = models.CharField(_('Адреса'), max_length=200, blank=True)

    class Meta:
        verbose_name = _('Клієнт')
        verbose_name_plural = _('Клієнти')

    def __str__(self):
        return self.user.get_full_name() or self.user.email or self.user.username
