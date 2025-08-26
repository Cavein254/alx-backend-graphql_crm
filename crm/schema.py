import graphene
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from .models import Customer, Product, Order
from .filters import CustomerFilter, ProductFilter, OrderFilter
from django.core.exceptions import ValidationError
from django.db import transaction
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation



# =====================
# GraphQL Types
# =====================
class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        # fields = ("id", "name", "email", "phone")
        interfaces = (graphene.relay.Node,)
        filterset_class = CustomerFilter


class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        fields = ("id", "name", "price", "stock")
        interfaces = (graphene.relay.Node,)
        filterset_class = ProductFilter


class OrderType(DjangoObjectType):
    class Meta:
        model = Order
        fields = ("id", "customer", "products", "total_amount", "order_date")
        interfaces = (graphene.relay.Node,)
        filterset_class = OrderFilter

# =====================
# Input Types
# =====================
class CustomerInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    email = graphene.String(required=True)
    phone = graphene.String()

class ProductInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    price = graphene.Float(required=True)
    stock = graphene.Int(default_value=0)


class OrderInput(graphene.InputObjectType):
    customer_id = graphene.ID(required=True)
    product_ids = graphene.List(graphene.ID, required=True)
    order_date = graphene.DateTime()


# =====================
# Mutations
# =====================
class CreateCustomer(graphene.Mutation):
    class Arguments:
        input = CustomerInput(required=True)

    customer = graphene.Field(CustomerType)
    message = graphene.String()
    errors = graphene.List(graphene.String)

    def mutate(self, info,input):
        errors = []
        # Email uniqueness
        if Customer.objects.filter(email=input.email).exists():
            errors.append(f"Email already exists: {input.email}")

        # Phone validation
        if input.phone:
            if not re.match(r"^\+?\d{1,3}[- ]?\d{3,}[- ]?\d{3,}$", input.phone):
                errors.append(f"Invalid phone format: {input.phone}")

        if errors:
            return CreateCustomer(customer=None, message="Failed to create customer", errors=errors)

        customer = Customer(
            name=input.name, 
            email=input.email, 
            phone=input.phone)
        customer.save()
        return CreateCustomer(customer=customer, message="Customer created successfully", errors=None)


class BulkCreateCustomers(graphene.Mutation):
    class Arguments:
        input = graphene.List(CustomerInput, required=True)

    customers = graphene.List(CustomerType)
    errors = graphene.List(graphene.String)

    @transaction.atomic
    def mutate(self, info, input):
        created_customers = []
        errors = []

        for data in input:
            try:
                # Notice: now we access fields as attributes (not dict keys)
                if Customer.objects.filter(email=data.email).exists():
                    errors.append(f"Email already exists: {data.email}")
                    continue

                if data.phone and not re.match(r"^\+?\d{1,3}[- ]?\d{3,}[- ]?\d{3,}$", data.phone):
                    errors.append(f"Invalid phone format: {data.phone}")
                    continue

                customer = Customer(name=data.name, email=data.email, phone=data.phone)
                customer.save()
                created_customers.append(customer)
            except Exception as e:
                errors.append(str(e))

        return BulkCreateCustomers(customers=created_customers, errors=errors)



class CreateProduct(graphene.Mutation):
    class Arguments:
        input = ProductInput(required=True)

    product = graphene.Field(ProductType)
    errors = graphene.List(graphene.String)

    def mutate(self, info, input):
        errors = []
        # Safely convert float to Decimal
        try:
            price_decimal = Decimal(str(input.price))
        except (InvalidOperation, ValueError):
            errors.append("Invalid price format. Must be a valid number.")

        if input.price <= 0:
            errors.append("Price must be positive.")
        if input.stock < 0:
            errors.append("Stock cannot be negative.")
        if errors:
            return CreateProduct(product=None, errors=errors)

        product = Product(name=input.name, price=price_decimal, stock=input.stock)
        product.save()
        return CreateProduct(product=product, errors=None)


class CreateOrder(graphene.Mutation):
    class Arguments:
        input = OrderInput(required=True)

    order = graphene.Field(OrderType)
    errors = graphene.List(graphene.String)

    def mutate(self, info, input):
        errors = []
        try:
            customer = Customer.objects.get(id=input.customer_id)
        except Customer.DoesNotExist:
            errors.append(f"Invalid customer ID: {input.customer_id}")
            return CreateOrder(order=None, errors=errors)


        products = []
        for pid in input.product_ids:
            try:
                product = Product.objects.get(id=pid)
                products.append(product)
            except Product.DoesNotExist:
                errors.append(f"Invalid product ID: {pid}")

        if not products:
            errors.append("No valid products provided")

        if errors:
            return CreateOrder(order=None, errors=errors)
        total_amount = sum(p.price for p in products)
        
        order = Order(
            customer=customer, 
            order_date=input.order_date or datetime.now())
        order.save()
        
        order.products.set(products)
        total = sum([p.price for p in products], Decimal("0.00"))
        order.total_amount = total
        order.save()

        return CreateOrder(order=order, errors=None)
class UpdateLowStockProducts(graphene.Mutation):
    class Arguments:
        # no input args, just restock all low-stock products
        pass

    updated_products = graphene.List(ProductType)
    message = graphene.String()

    def mutate(self, info):
        low_stock_products = Product.objects.filter(stock__lt=10)
        updated = []
        for product in low_stock_products:
            product.stock += 10  # simulate restocking
            product.save()
            updated.append(product)

        return UpdateLowStockProducts(
            updated_products=updated,
            message="Low-stock products have been restocked successfully!"
        )

class Mutation(graphene.ObjectType):
    update_low_stock_products = UpdateLowStockProducts.Field()
    
# =====================
# Root Mutation + Query
# =====================
class Query(graphene.ObjectType):
    hello = graphene.String(default_value="Hello, GraphQL!")
    all_customers = DjangoFilterConnectionField(CustomerType)
    all_products = DjangoFilterConnectionField(ProductType)
    all_orders = DjangoFilterConnectionField(OrderType)
    # -------------------- Customers --------------------
    customers = graphene.List(
        CustomerType,
        name=graphene.String(),
        email=graphene.String()
    )
    
    # -------------------- Products --------------------
    products = graphene.List(
        ProductType,
        name=graphene.String(),
        price_gte=graphene.Float(),
        price_lte=graphene.Float(),
        stock_gte=graphene.Int(),
        stock_lte=graphene.Int()
    )

    # -------------------- Orders --------------------
    orders = graphene.List(
        OrderType,
        total_amount_gte=graphene.Float(),
        total_amount_lte=graphene.Float(),
        customer_name=graphene.String(),
        product_name=graphene.String()
    )


    def resolve_customers(self, info, name=None, email=None):
        qs = Customer.objects.all()
        if name:
            qs = qs.filter(name__icontains=name)
        if email:
            qs = qs.filter(email__icontains=email)
        return qs


    def resolve_products(self, info, name=None, price_gte=None, price_lte=None, stock_gte=None, stock_lte=None):
        qs = Product.objects.all()
        if name:
            qs = qs.filter(name__icontains=name)
        if price_gte is not None:
            qs = qs.filter(price__gte=price_gte)
        if price_lte is not None:
            qs = qs.filter(price__lte=price_lte)
        if stock_gte is not None:
            qs = qs.filter(stock__gte=stock_gte)
        if stock_lte is not None:
            qs = qs.filter(stock__lte=stock_lte)
        return qs

    def resolve_orders(self, info, total_amount_gte=None, total_amount_lte=None, customer_name=None, product_name=None):
        qs = Order.objects.select_related("customer").prefetch_related("products").all()
        if total_amount_gte is not None:
            qs = qs.filter(total_amount__gte=total_amount_gte)
        if total_amount_lte is not None:
            qs = qs.filter(total_amount__lte=total_amount_lte)
        if customer_name:
            qs = qs.filter(customer__name__icontains=customer_name)
        if product_name:
            qs = qs.filter(product__name__icontains=product_name)
        return qs

class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()

