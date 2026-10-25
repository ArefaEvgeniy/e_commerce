import pytest
import sys

from django.urls import reverse


def test_product_list(client, db):
    response = client.get(reverse("product_list"))

    assert response.status_code == 301


def test_product_list_template(client, db):
    response = client.get(reverse("product_list"))

    assert response.status_code == 301
    # assert "product/list.html" in [
    #     template.name for template in response.templates
    # ]


def test_product_list_context(client, db):
    response = client.get(reverse("product_list"))

    assert response.status_code == 301
    # assert "products" in response.context


def test_cart_add(client, product, settings):
    response = client.post(
        reverse("cart_add", kwargs={"product_id": product.id}),
        {"quantity": 2},
    )

    assert response.status_code == 301
    # assert response.url == reverse("cart_detail")
    #
    # session = client.session
    # assert str(product.id) in session[settings.CART_SESSION_ID]
    #
    # cart = client.session[settings.CART_SESSION_ID]
    # assert cart[str(product.id)]["quantity"] == 2


@pytest.mark.skip(reason="Функція ще не готова")
def test_order_back(client):
    pass


@pytest.mark.skipif(
    sys.platform == "win32",
    reason="Этот тест предназначен для Linux",
)
def test_linux_feature():
    ...
