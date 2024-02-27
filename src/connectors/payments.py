import logging

import stripe

from src.core.config import get_settings

setttings = get_settings()

stripe.api_key = setttings.STRIPE_SECRET_KEY

logger = logging.getLogger(__name__)


class PaymentService:
    def __init__(self) -> None:
        pass

    def get_products(self):
        products = stripe.Product.list()
        return products.data

    def create_product(self, name, description):
        product = stripe.Product.create(
            name=name,
            description=description,
        )
        return product

    def create_price(self, product_id, amount, currency="usd"):
        price = stripe.Price.create(
            product=product_id,
            unit_amount=amount,
            currency=currency,
        )
        return price

    def get_or_customer(self, email):
        # If email exists get it else create it
        customer = stripe.Customer.list(email=email)

        if len(customer) == 0:
            customer = stripe.Customer.create(
                email=email,
                name=email,
            )

        if len(customer) >= 2:
            logger.error("More than one customer found")
            return customer.data[0]

        return customer.data[0]

    def get_prices(self, product_id):
        prices = stripe.Price.list(product=product_id)
        # Sort by increasing prices (lowest first)
        prices.data.sort(key=lambda x: x.unit_amount)
        return prices.data

    def create_invoice(self, customer_id, product_id, price_id):
        # Create an Invoice
        invoice = stripe.Invoice.create(
            customer=customer_id,
            collection_method="send_invoice",
            days_until_due=30,
        )

        # Add the product to the invoice
        stripe.InvoiceItem.create(
            customer=customer_id,
            price=price_id,
            quantity=1,
            invoice=invoice.id,
        )

        # Get the link
        invoice = stripe.Invoice.finalize_invoice(invoice.id)

        return invoice

    def get_payment_history(self, customer_id):
        # Get payment history from Stripe
        payments = stripe.PaymentIntent.list(customer=customer_id)
        return payments.data

    def get_invoice_history(self, customer_id):
        invoice_history = stripe.Invoice.list(customer=customer_id)
        return invoice_history.data

    def get_invoice(self, invoice_id):
        invoice = stripe.Invoice.retrieve(invoice_id)
        return invoice

    def get_last_payments(self, limit=50):
        payments = stripe.PaymentIntent.list(limit=limit)
        return payments.data
