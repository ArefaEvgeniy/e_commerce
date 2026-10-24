import pytest
from decimal import Decimal

from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory

from shop.models import Product, Category


@pytest.fixture
def django_request(db):
    request = RequestFactory().get("/")

    middleware = SessionMiddleware(lambda request: None)
    middleware.process_request(request)
    request.session.save()

    return request


@pytest.fixture
def category(db):
    return Category.objects.create(
        name="Test category",
    )


@pytest.fixture
def product(db, category):
    return Product.objects.create(
        name="Test product",
        slug="test-product",
        description="Test description",
        category=category,
        price=Decimal("100.00"),
    )
