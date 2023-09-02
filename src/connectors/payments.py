import stripe

from src.core.config import get_settings

setttings = get_settings()

stripe.api_key = setttings.STRIPE_SECRET_KEY

CUSTOMERS = [{"stripe_id": "cus_123456789", "email": "jenny.rosen@example.com"}]
PRICES = {"basic": "price_123456789", "professional": "price_987654321"}


def send_invoice(email, products):
    # Look up a customer in your database
    customers = [c for c in CUSTOMERS if c["email"] == email]

    # Get the products list from Stripe

    products_list = stripe.Product.list()

    # If the products list is empty, create the products
    if not products:
        for product in products_list:
            stripe.Product.create(
                name=product["name"],
                description=product["description"],
            )

    if customers:
        customer_id = customers[0]["stripe_id"]
    else:
        # Create a new Customer
        customer = stripe.Customer.create(
            email=email,  # Use your email address for testing purposes
            description="Customer to invoice",
        )
        # Store the customer ID in your database for future purchases
        CUSTOMERS.append({"stripe_id": customer.id, "email": email})
        # Read the Customer ID from your database
        customer_id = customer.id

    # Create an Invoice
    invoice = stripe.Invoice.create(
        customer=customer_id,
        collection_method="send_invoice",
        days_until_due=30,
    )

    # Create an Invoice Item with the Price and Customer you want to charge
    stripe.InvoiceItem.create(
        customer=customer_id, price=PRICES["basic"], invoice=invoice.id
    )

    # Send the Invoice
    stripe.Invoice.send_invoice(invoice.id)
    return


if __name__ == "__main__":
    send_invoice("ayo.enn@gmail.com")
