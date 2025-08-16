from django.core.management.base import BaseCommand
from crm.models import Customer, Product, Order
from faker import Faker
from decimal import Decimal
import random
import datetime

fake = Faker()

class Command(BaseCommand):
    help = "Seed the database with fake customers, products, and orders."

    def add_arguments(self, parser):
        parser.add_argument('--customers', type=int, default=10, help='Number of customers to create')
        parser.add_argument('--products', type=int, default=20, help='Number of products to create')
        parser.add_argument('--orders', type=int, default=30, help='Number of orders to create')

    def handle(self, *args, **options):
        customers_count = options['customers']
        products_count = options['products']
        orders_count = options['orders']

        self.stdout.write(self.style.SUCCESS(f"Seeding {customers_count} customers, {products_count} products, {orders_count} orders..."))

        # Customers
        customers = []
        for _ in range(customers_count):
            customer = Customer(
                name=fake.name(),
                email=fake.unique.email(),
                phone=fake.phone_number(),
            )
            customer.save()
            customers.append(customer)

        # Products
        products = []
        for _ in range(products_count):
            product = Product(
                name=fake.word().capitalize(),
                price=Decimal(str(round(random.uniform(10.0, 2000.0), 2))),
                stock=random.randint(0, 50),
            )
            product.save()
            products.append(product)

        # Orders
        for _ in range(orders_count):
            customer = random.choice(customers)
            selected_products = random.sample(products, k=random.randint(1, min(5, len(products))))

            order = Order(
                customer=customer,
                order_date=fake.date_time_between(start_date="-1y", end_date="now"),
                total_amount=Decimal("0.00")
            )
            order.save()  # Must save before adding M2M

            order.products.set(selected_products)

            total = sum([p.price for p in selected_products], Decimal("0.00"))
            order.total_amount = total
            order.save()

        self.stdout.write(self.style.SUCCESS("✅ Seeding complete!"))
