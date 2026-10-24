import logging

from botocore.exceptions import ClientError
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

from shop.models import Product, Customer
from shop.orders.models import Order, OrderItem
from shop.cart.cart import Cart
from shop.forms import OrderCreateForm
from shop.tasks import test_task, send_order_confirmation_email
from shop.boto_client import get_s3_client, FILE_BUCKET_NAME


logging = logging.getLogger(__name__)


def product_list(request):
    products = Product.active.all()
    user_id = None
    if request.user.is_authenticated:
        user_id = request.user.id
    test_task.delay(user_id)
    return render(request, 'product/list.html', {'products': products})


def cart_detail(request):
    cart = Cart(request)
    context = {
        'cart': cart,
        'total_price': cart.get_total_price()
    }
    return render(request, 'cart/detail.html', context)


def cart_add(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id, is_active=True)

    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        cart.add(product=product, quantity=quantity, override_quantity=False)
        messages.success(request, f'Товар "{product.name}" додано до кошика.')
        return redirect('cart_detail')


def cart_remove(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id, is_active=True)
    cart.remove(product)
    messages.info(request, f'Товар "{product.name}" видалено з кошика.')
    return redirect('cart_detail')


def cart_clear(request):
    cart = Cart(request)
    cart.clear()
    messages.info(request, 'Кошик очищено.')
    return redirect('cart_detail')


def order_create(request):
    cart = Cart(request)
    if not cart or len(cart) == 0:
        messages.warning(request, 'Ваш кошик порожній.')
        return redirect('cart_detail')

    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.total_price = cart.get_total_price()

            if request.user.is_authenticated:
                try:
                    order.customer = request.user.customer
                except Exception:
                    customer, created = Customer.objects.get_or_create(user=request.user)
                    order.customer = customer
            order.save()

            for item in cart:
                OrderItem.objects.create(
                    order=order,
                    product=item['product'],
                    quantity=item['quantity'],
                    price=item['product'].current_price
                )

            cart.clear()
            messages.success(request, f'Ваше замовлення #{order.id} успішно створено.')
            send_order_confirmation_email.delay(order.id)
            return render(request, 'order/success_order.html', {'order': order})

    else:
        initial_data = {}
        if request.user.is_authenticated:
            user = request.user
            initial_data = {
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
            }
            customer = getattr(user, 'customer_profile', None)
            if customer:
                customer = user.customer_profile
                initial_data.update(
                    {
                    'phone': customer.phone,
                    'address': customer.address,
                    }
                )

        form = OrderCreateForm(initial=initial_data)

    context = {
        'form': form,
        'cart': cart,
        'total_price': cart.get_total_price()
    }

    return render(request, 'order/create_order.html', context)


def upload_s3_files(request):
    if request.method == 'POST' and request.FILES['file']:
        file = request.FILES['file']
        default_storage.save(file.name, ContentFile(file.read()))
    return redirect('s3_files_list')


def s3_files_list(request):
    s3_client = get_s3_client()
    s3_public_client = get_s3_client(
        settings.AWS_S3_PUBLIC_ENDPOINT_URL
    )
    files = []
    errors = []
    continuation_token = None

    try:
        while True:
            params = {'Bucket': FILE_BUCKET_NAME}
            if continuation_token:
                params['ContinuationToken'] = continuation_token
            response = s3_client.list_objects_v2(**params)
            for file in response.get('Contents', []):
                file_name = file['Key']
                try:
                    file_params = params.copy()
                    file_params['Key'] = file_name
                    presigned_file_url = s3_public_client.generate_presigned_url(
                        'get_object',
                        Params={'Bucket': FILE_BUCKET_NAME, 'Key': file_name},
                        ExpiresIn=3600
                    )
                    files.append({
                        'file_name': file_name,
                        'file_url': presigned_file_url,
                        'size': file['Size'],
                        'last_modified': file['LastModified'],
                    })
                except ClientError as err:
                    errors.append(err)
                    logging.error(f"Failed to list S3 files: {err}")
            if response.get('IsTruncated'):
                continuation_token = response.get('NextContinuationToken')
            else:
                break
    except ClientError as err:
        errors.append(err)
        logging.error(f"Failed to list S3 files: {err}")

    return render(request, 's3_bucket/s3_files_list.html', {'files': files, 'errors': errors})
