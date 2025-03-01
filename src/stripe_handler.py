import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import stripe
from dotenv import load_dotenv
from flask import current_app, redirect, url_for
from stripe import ErrorObject, StripeError

load_dotenv()

# will use a user class to get more info about the user to create a customer

SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")


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
            response = stripe.Customer.delete(customer_id)
            return response.get("deleted", False)
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
            current_app.logger.error(
                f"Stripe Error (create_customer_session): {e}")
            return None

    def create_checkout_session(self):
        DOMAIN = "https://localhost:5000"
        try:
            session = stripe.checkout.Session.create(
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
                success_url=DOMAIN + '/payment_success',
                cancel_url=DOMAIN + '/payment_cancel',
            )

        except StripeError as e:
            current_app.logger.error(
                f"Stripe Error (create_checkout_session): {e}")
            return None
        return redirect(session.url, code=303)

    def check_checkout_session(self, session_id):
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            # Returns the whole session and the status 'open', 'complete', or 'expired'
            return (session, session.status)
        except StripeError as e:
            current_app.logger.error(
                f"Stripe Error (check_checkout_session): {e}")
            return None

    def handle_payment(self, session):
        # if the payment is successful, send the user a confirmation email, do not handle unsuccessful payments
        if not EMAIL_USER or not EMAIL_PASS or not SMTP_SERVER or not SMTP_PORT:
            current_app.logger.error(
                "EMAIL_USER or EMAIL_PASS or SMTP_SERVER or SMTP_PORT is not set")
            return None
        customer_email = session["customer_email"]
        product_price = session["amount_total"]
        message = MIMEMultipart()
        message["From"] = EMAIL_USER
        message["To"] = customer_email
        message["Subject"] = f"Payment Successful {"item"}"
        message.attach(MIMEText(f"""
            <h1>Payment Successful for {"item"}</h1>
            <p>Dear {customer_email},</p>
            <p>Thank you for your purchase <b>{"item"}</b>.
            <p>Your payment of <b>${product_price / 100}</b> has been successfully processed.</p>
            <p>If you have any questions, please contact us at <a href="mailto:uvmhackathon2025@gmail.com">uvmhackathon2025@gmail.com</a>.</p>
            <p>Thank you for your purchase!</p>
            """
        ))
        session = self.check_checkout_session(session["id"])
        if session is not None and session[1] == "complete":
            # send the email
            try:
                current_app.logger.info(f"Sending email to {customer_email}")
                with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                    server.starttls()
                    server.login(EMAIL_USER, EMAIL_PASS)
                    server.sendmail(message["From"],
                                    message["To"], message.as_string())
                    current_app.logger.info(f"Email sent to {customer_email}")
                return True
            except Exception as e:
                current_app.logger.error(f"Error sending email: {e}")
                return False
        else:
            current_app.logger.info(f"Payment not successful")
            return False
