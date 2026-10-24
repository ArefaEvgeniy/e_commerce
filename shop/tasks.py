from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model

from shop.orders.models import Order
from shop.models import Product


User = get_user_model()


@shared_task
def test_task(user_id: int|None):
    user = None
    if user_id:
        user = User.objects.filter(id=user_id).first()
    requested_user = user.username if user else "Not authenticated User"
    return f"Test task executed successfully! Requested by: {requested_user}"


@shared_task
def send_order_confirmation_email(order_id: int):
    try:
        order = Order.objects.prefetch_related('items__product').get(pk=order_id)
    except Order.DoesNotExist:
        return f'Order with ID {order_id} does not exist.'

    items_text = "\n".join([
        f"{item.quantity} x {item.product.name} - {item.get_total_price()} UAH"
        for item in order.items.all()
    ])

    subject = f"Order Confirmation - Order #{order.id}"

    message = f"""
    Dear {order.first_name} {order.last_name},
    Thank you for your order! Here are the details of your purchase:
    Order ID: {order.id}
    Items:
    {items_text}
    Total Price: {order.total_price} UAH
    We will notify you once your order is shipped.
    Best regards,
    Your Shop Team
    """

    try:
        send_mail(
            subject=subject,
            message=message,
            recipient_list=[order.email],
            from_email=settings.DEFAULT_EMAIL_FROM,
        )
    except Exception as e:
        return f"Failed to send email: {str(e)}"

    return f"Order confirmation email sent successfully to {order.email} for Order ID {order.id}."


@shared_task
def notify_low_stock_products():
    low_stock = list(
        Product.objects.filter(
            is_active=True,
            stock__lte=settings.LOW_STOCK_THRESHOLD
        ).values('id', 'name', 'stock')
    )

    if not low_stock:
        return {'notified': 0, 'products': []}

    staff_emails = list(
        User.objects.filter(
            is_staff=True,
            is_active=True
        ).values_list('email', flat=True)
    )

    if not staff_emails:
        return {'notified': 0, 'products': low_stock}

    lines = '\n'.join([
        f"{product['name']} (ID: {product['id']}) - Stock: {product['stock']}"
        for product in low_stock
    ])

    send_mail(
        subject=f"Low Stock Alert for {len(low_stock)} Products",
        message=f"The following products are low in stock:\n\n{lines}",
        from_email=settings.DEFAULT_EMAIL_FROM,
        recipient_list=staff_emails,
    )

    return {'notified': len(staff_emails), 'products': low_stock}
