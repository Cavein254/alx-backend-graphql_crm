import graphene
from graphene_django import DjangoObjectType
from .models import Customer, Product, Order
from django.core.exceptions import ValidationError
from django.db import transaction
import re
from datetime import datetime



# =====================
# GraphQL Types
# =====================
class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        fields = ("id", "name", "email", "phone")


class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        fields = ("id", "name", "price", "stock")


class OrderType(DjangoObjectType):
    class Meta:
        model = Order
        fields = ("id", "customer", "products", "total_amount", "order_date")

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
        # Email uniqueness
        if Customer.objects.filter(email=input.email).exists():
            raise Exception("Email already exists")

        # Phone validation
        if input.phone:
            if not re.match(r"^\+?\d{1,3}[- ]?\d{3,}[- ]?\d{3,}$", input.phone):
                raise Exception("Invalid phone format. Use +1234567890 or 123-456-7890")

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
    def mutate(self, info, customers):
        created_customers = []
        errors = []

        for data in customers:
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
        if input.price <= 0:
            raise Exception("Price must be positive")
        if input.stock < 0:
            raise Exception("Stock cannot be negative")

        product = Product(name=input.name, price=input.price, stock=input.stock)
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
        
        order = Order(
            customer=customer, 
            order_date=input.order_date or datetime.now()
            total_amount=total_amount)
        
        order.products.set(products)

        return CreateOrder(order=order, errors=None)

# =====================
# Root Mutation + Query
# =====================
class Query(graphene.ObjectType):
    hello = graphene.String(default_value="Hello, GraphQL!")
    customers = graphene.List(CustomerType)
    products = graphene.List(ProductType)
    orders = graphene.List(OrderType)

    def resolve_customers(self, info):
        return Customer.objects.all()

    def resolve_products(self, info):
        return Product.objects.all()

    def resolve_orders(self, info):
        return Order.objects.all()


class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()

