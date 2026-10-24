from decimal import Decimal
from rest_framework import serializers
from shop.models import Product, Category
from shop.orders.models import Order, OrderItem


class CategorySerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'parent', 'is_active', 'children']

    def get_children(self, obj):
        active_children = obj.children.filter(is_active=True)
        return CategorySerializer(active_children, many=True).data


class ProductSerializer(serializers.ModelSerializer):
    current_price = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )
    category_name = serializers.CharField(
        source='category.name', read_only=True
    )

    class Meta:
        model = Product
        fields = [
            'id',
            'name',
            'slug',
            'description',
            'category',
            'price',
            'discount_price',
            'stock',
            'is_active',
            'category_name',
            'current_price'
        ]


class ProductDetailSerializer(serializers.ModelSerializer):
    current_price = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )
    category = CategorySerializer(read_only=True)

    class Meta:
        model = Product
        fields = [
            'id',
            'name',
            'slug',
            'description',
            'category',
            'price',
            'discount_price',
            'stock',
            'is_active',
            'current_price',
            'created_at',
            'updated_at'
        ]
