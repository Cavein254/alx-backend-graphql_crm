# crm/filters.py
import django_filters
from .models import Customer, Product, Order

class CustomerFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(field_name="name", lookup_expr="icontains")
    email = django_filters.CharFilter(field_name="email", lookup_expr="icontains")
    phone = django_filters.CharFilter(field_name="phone", lookup_expr="icontains")

    class Meta:
        model = Customer
        fields = ["name", "email", "phone"]




class ProductFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(field_name="name", lookup_expr="icontains")
    price__gte = django_filters.NumberFilter(field_name="price", lookup_expr="gte")
    price__lte = django_filters.NumberFilter(field_name="price", lookup_expr="lte")
    stock__gte = django_filters.NumberFilter(field_name="stock", lookup_expr="gte")
    stock__lte = django_filters.NumberFilter(field_name="stock", lookup_expr="lte")

    class Meta:
        model = Product
        fields = ["name", "price", "stock"]


class OrderFilter(django_filters.FilterSet):
    total_amount__gte = django_filters.NumberFilter(field_name="total_amount", lookup_expr="gte")
    total_amount__lte = django_filters.NumberFilter(field_name="total_amount", lookup_expr="lte")
    order_date__gte = django_filters.DateFilter(field_name="order_date", lookup_expr="gte")
    order_date__lte = django_filters.DateFilter(field_name="order_date", lookup_expr="lte")
    customer_name = django_filters.CharFilter(field_name="customer__name", lookup_expr="icontains")
    product_name = django_filters.CharFilter(field_name="products__name", lookup_expr="icontains")
    product_id = django_filters.NumberFilter(field_name="products__id", lookup_expr="exact")

    class Meta:
        model = Order
        fields = ["total_amount", "order_date"]
