import pytest

from shop.models import Category


@pytest.mark.django_db
def test_create_category():
    category = Category.objects.create(
        name="Phones",
        slug="phones",
    )

    assert category.name == "Phones"
    assert category.slug == "phones"
    assert category.is_active is True


@pytest.mark.django_db
def test_category_str():
    category = Category.objects.create(
        name="Phones",
        slug="phones",
    )

    assert str(category) == "Phones"


@pytest.mark.django_db
def test_category_parent():
    parent = Category.objects.create(
        name="Electronics",
        slug="electronics",
    )

    child = Category.objects.create(
        name="Phones",
        slug="phones",
        parent=parent,
    )

    assert child.parent == parent
