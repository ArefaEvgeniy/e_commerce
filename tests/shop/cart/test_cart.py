from decimal import Decimal

from shop.cart.cart import Cart


def test_cart_initialization(django_request, settings):
    cart = Cart(django_request)

    assert cart.cart == {}
    assert settings.CART_SESSION_ID in django_request.session


def test_add_product(django_request, product):
    cart = Cart(django_request)

    cart.add(product)

    product_id = str(product.id)

    assert product_id in cart.cart
    assert cart.cart[product_id]["quantity"] == 1
    assert cart.cart[product_id]["price"] == str(product.current_price)


def test_add_product_with_quantity(django_request, product):
    cart = Cart(django_request)

    cart.add(product, quantity=3)

    product_id = str(product.id)

    assert cart.cart[product_id]["quantity"] == 3


def test_add_product_twice(django_request, product):
    cart = Cart(django_request)

    cart.add(product, quantity=2)
    cart.add(product, quantity=3)

    product_id = str(product.id)

    assert cart.cart[product_id]["quantity"] == 5


def test_add_product_override_quantity(django_request, product):
    cart = Cart(django_request)

    cart.add(product, quantity=2)
    cart.add(product, quantity=7, override_quantity=True)

    product_id = str(product.id)

    assert cart.cart[product_id]["quantity"] == 7


def test_add_product_with_zero_quantity(django_request, product):
    cart = Cart(django_request)

    cart.add(product, quantity=0)

    product_id = str(product.id)

    assert cart.cart[product_id]["quantity"] == 1


def test_add_product_with_negative_quantity(django_request, product):
    cart = Cart(django_request)

    cart.add(product, quantity=-5)

    product_id = str(product.id)

    assert cart.cart[product_id]["quantity"] == 1


def test_get_total_price(django_request, product):
    cart = Cart(django_request)

    cart.add(product, quantity=3)

    assert cart.get_total_price() == Decimal("300.00")
