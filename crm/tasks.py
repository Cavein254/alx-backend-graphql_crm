from datetime import datetime
import requests
from celery import shared_task
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

@shared_task
def generate_crm_report():
    """Generate a weekly CRM report using GraphQL data."""

    transport = RequestsHTTPTransport(
        url="http://localhost:8000/graphql",
        verify=False,
        retries=3,
    )
    client = Client(transport=transport, fetch_schema_from_transport=True)

    query = gql("""
        query {
            totalCustomers
            totalOrders
            totalRevenue
        }
    """)

    try:
        result = client.execute(query)
        customers = result.get("totalCustomers", 0)
        orders = result.get("totalOrders", 0)
        revenue = result.get("totalRevenue", 0)

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open("/tmp/crm_report_log.txt", "a") as log:
            log.write(f"{timestamp} - Report: {customers} customers, {orders} orders, {revenue} revenue\n")
    except Exception as e:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open("/tmp/crm_report_log.txt", "a") as log:
            log.write(f"{timestamp} - ERROR generating report: {e}\n")
