import logging

import stripe

from src.core.config import get_settings

setttings = get_settings()

stripe.api_key = setttings.STRIPE_SECRET_KEY

logger = logging.getLogger(__name__)


def get_custom_fields(checkout, field_name):
    custom_fields = checkout.get("custom_fields", [])
    for field in custom_fields:
        if field.get("key") == field_name:
            return field.get("text").get("value")
    return None


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

    def get_last_payments(self, limit=3):
        """
                expand[]: source
        expand[]: customer
        expand[]: invoice
        expand[]: payment_method
        expand[]: charges.data.customer
        expand[]: charges.data.refunds.total_count
        expand[]: latest_charge.customer
        expand[]: latest_charge.refunds.total_count
        expand[]: charges.data.refunds.data.balance_transaction.automatic_transfer
        expand[]: latest_charge.refunds.data.balance_transaction.automatic_transfer
        expand[]: charges.data.balance_transaction.automatic_transfer
        expand[]: latest_charge.balance_transaction.automatic_transfer
        expand[]: charges.data.dispute.balance_transactions.automatic_transfer
        expand[]: latest_charge.dispute.balance_transactions.automatic_transfer
        expand[]: charges.data.review
        expand[]: latest_charge.review
        expand[]: charges.data.application_fee
        expand[]: latest_charge.application_fee
        expand[]: charges.data.early_fraud_warning
        expand[]: latest_charge.early_fraud_warning
        """

        payments = stripe.PaymentIntent.list(
            limit=limit,
            expand=[
                "data.customer",
                "data.invoice",
                "data.payment_method",
                "data.charges.data.customer",
            ],
        )
        return payments.data

    def get_last_checkouts(self, limit=30):
        checkout_sessions = stripe.checkout.Session.list(
            limit=limit,
            status="complete",
            expand=[
                "data.customer",
                "data.invoice",
            ],
        )
        return checkout_sessions.data

    def get_checkout(self, checkout_id):
        checkout = stripe.checkout.Session.retrieve(checkout_id)
        return checkout
