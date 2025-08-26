#!/usr/bin/env python3
import datetime
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

# GraphQL endpoint
transport = RequestsHTTPTransport(
    url="http://localhost:8000/graphql",
    verify=False,
    retries=3,
)

client = Client(transport=transport, fetch_schema_from_transport=True)

# Calculate cutoff date (7 days ago)
cutoff_date = (datetime.datetime.now() - datetime.timedelta(days=7)).strftime("%Y-%m-%d")

# GraphQL query
query = gql("""
    query GetRecentOrders($cutoff: Date!) {
        orders(orderDate_Gte: $cutoff) {
            id
            customer {
                email
            }
        }
    }
""")

# Execute query
result = client.execute(query, variable_values={"cutoff": cutoff_date})

orders = result.get("orders", [])

# Log to file
with open("/tmp/order_reminders_log.txt", "a") as log:
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for order in orders:
        log.write(f"{timestamp} - Order ID: {order['id']}, Customer Email: {order['customer']['email']}\n")

print("Order reminders processed!")
