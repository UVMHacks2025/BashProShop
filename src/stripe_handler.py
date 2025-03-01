import stripe
from stripe import ErrorObject, StripeError
import os
from flask import current_app
# will use a user class to get more info about the user to create a customer


class StripeHandler:
    def __init__(self):
        self.api_key = os.getenv("STRIPE_SECRET_KEY")

        if not self.api_key:
            raise ValueError("STRIPE_SECRET_KEY is not set")
        
        stripe.api_key = self.api_key

    def create_customer_params(self, user):
        params = {
            "email": user["email"],
            "name": user["name"],
            "phone": user["phone"],
            "address": user["address"],
            "metadata": user.get("metadata", {}),
        }
        return params

    def create_customer(self, params):
        try:
            customer = stripe.Customer.create(**params)
            return customer
        except StripeError as e:
            current_app.logger.error(f"Stripe error: {e}")
            return None

    def get_customer(self, customer_id):
        try:
            customer = stripe.Customer.retrieve(customer_id)
            return customer
        except StripeError as e:
            current_app.logger.error(f"Stripe error: {e}")
            return None
    
    def get_all_customers(self):
        try:
            customers = stripe.Customer.list()
            return customers
        except StripeError as e:
            current_app.logger.error(f"Stripe error: {e}")
            return None
    
    def update_customer(self, customer_id, params):
        try:
            customer = stripe.Customer.modify(customer_id, **params)
            return customer
        except StripeError as e:
            current_app.logger.error(f"Stripe error: {e}")
            return None
    
    def delete_customer(self, customer_id):
        try:
            stripe.Customer.delete(customer_id)
        except StripeError as e:
            current_app.logger.error(f"Stripe error: {e}")
            return None
    
    def customers_query(self, query: str):
        try:
            customers = stripe.Customer.search(query=query)
            return customers
        except StripeError as e:
            current_app.logger.error(f"Stripe error: {e}")
            return None
    
    def create_customer_session(self, customer_id):
        try: 
            session = stripe.CustomerSession.create(
                customer=customer_id,
                components={
                    "pricing_table": {
                        "enabled": True,
                    },
                    # "buy_button": {
                    #     "enabled": True,
                    # },
                    # "payment_element": {
                    #     "enabled": True,
                    # },
                },
            )
            return session
        except StripeError as e:
            current_app.logger.error(f"Stripe Error (create_customer_session): {e}")
            return None
    
    def create_checkout_session(self, customer_id, success_url, cancel_url):
        try:
            session = stripe.checkout.Session.create(
                customer=customer_id,
                payment_method_types=['card'],
                mode="payment",
                line_items=[{
                    "price_data": {
                        "currency": "usd",
                        "product_data": {"name": "NEED TO FILL"},
                        "unit_amount": 1000,  # $10.00 in cents, will change as needed
                    },
                    "quantity": 1,
                }],
                success_url=success_url,
                cancel_url=cancel_url,
            )
            return session
        except StripeError as e:
            current_app.logger.error(f"Stripe Error (create_checkout_session): {e}")
            return None
