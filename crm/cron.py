import datetime
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport


def log_crm_heartbeat():
    """Log a heartbeat message and optionally ping GraphQL endpoint."""
    timestamp = datetime.datetime.now().strftime("%d/%m/%Y-%H:%M:%S")
    message = f"{timestamp} CRM is alive\n"

    # Append heartbeat to log file
    with open("/tmp/crm_heartbeat_log.txt", "a") as log:
        log.write(message)

    # Optional: Verify GraphQL hello field
    try:
        from gql import gql, Client
        from gql.transport.requests import RequestsHTTPTransport

        transport = RequestsHTTPTransport(
            url="http://localhost:8000/graphql",
            verify=False,
            retries=2,
        )
        client = Client(transport=transport, fetch_schema_from_transport=False)

        query = gql(""" query { hello } """)
        result = client.execute(query)
        with open("/tmp/crm_heartbeat_log.txt", "a") as log:
            log.write(f"{timestamp} GraphQL hello response: {result.get('hello', 'N/A')}\n")
    except Exception as e:
        with open("/tmp/crm_heartbeat_log.txt", "a") as log:
            log.write(f"{timestamp} GraphQL check failed: {e}\n")


def update_low_stock():
    """Execute GraphQL mutation to restock low-stock products and log updates."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    transport = RequestsHTTPTransport(
        url="http://localhost:8000/graphql",
        verify=False,
        retries=3,
    )
    client = Client(transport=transport, fetch_schema_from_transport=True)

    mutation = gql("""
        mutation {
            updateLowStockProducts {
                updatedProducts {
                    id
                    name
                    stock
                }
                message
            }
        }
    """)

    try:
        result = client.execute(mutation)
        updates = result["updateLowStockProducts"]["updatedProducts"]
        message = result["updateLowStockProducts"]["message"]

        with open("/tmp/low_stock_updates_log.txt", "a") as log:
            log.write(f"{timestamp} - {message}\n")
            for product in updates:
                log.write(f"   Product: {product['name']}, New Stock: {product['stock']}\n")
    except Exception as e:
        with open("/tmp/low_stock_updates_log.txt", "a") as log:
            log.write(f"{timestamp} - ERROR: {e}\n")