from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


def send_reciepe(email, order):
    html_content = render_to_string('email/order_receipt.html', {'order': order})
    email = EmailMultiAlternatives(
        subject=f'Замовлення #{order}',
        from_email=None,
        to=[email],
    )
    email.attach_alternative(html_content, "text/html")
    email.send()


def calculate_interest(amount, interest_rate, months):
    total_amount = round(amount * ((1 + interest_rate) ** months), 9)
    return total_amount
