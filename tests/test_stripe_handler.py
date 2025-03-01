import pytest
from src.stripe_handler import StripeHandler
from src.app import app
import stripe
from unittest.mock import patch, MagicMock
from dotenv import load_dotenv

@pytest.fixture
def setUp():
    load_dotenv()
    stripe_handler = StripeHandler()
    return stripe_handler

def test_create_customer_params(setUp):
    stripe_handler = setUp
    params = stripe_handler.create_customer_params({
        "email": "test@test.com",
        "name": "Test User",
        "address": "123 Main St, Anytown, USA",
        "phone": "123-456-7890",
    }) # empty metadata
    assert params is not None
    if params:
        assert params["email"] == "test@test.com"
        assert params["name"] == "Test User"
        assert params["address"] == "123 Main St, Anytown, USA"
        assert params["phone"] == "123-456-7890"
        assert params["metadata"] == {}
    params = stripe_handler.create_customer_params({
        "email": "test@test.com",
        "name": "Test User",
        "phone": "123-456-7890",
        "address": "123 Main St, Anytown, USA",
        "metadata": {"user_id": "123"}, # extra metadata
    })
    assert params is not None
    if params:
        assert params["email"] == "test@test.com"
        assert params["name"] == "Test User"
        assert params["address"] == "123 Main St, Anytown, USA"
        assert params["phone"] == "123-456-7890"
        assert params["metadata"] == {"user_id": "123"}

def test_create_customer(setUp):
    stripe_handler = setUp
    customer = stripe_handler.create_customer({
        "email": "test@test.com",
        "name": "Test User",
    })
    assert customer is not None
    if customer:
        assert customer.email == "test@test.com"
        assert customer.name == "Test User"

def test_get_customer(setUp):
    stripe_handler = setUp
    customer_instance = stripe_handler.create_customer({
        "email": "test@test.com",
        "name": "Test User",
    })
    if customer_instance:
        retrieved_customer = stripe_handler.get_customer(customer_instance.id)
        assert retrieved_customer is not None
        if retrieved_customer:
            assert retrieved_customer.email == "test@test.com"
            assert retrieved_customer.name == "Test User"

def test_get_all_customers(setUp):
    stripe_handler = setUp
    customers = stripe_handler.get_all_customers()
    assert customers is not None
    if customers:
        assert isinstance(customers, dict)
        assert len(customers) > 0
        for customer in customers:
            assert isinstance(customer, stripe.Customer)

def test_update_customer(setUp):
    stripe_handler = setUp
    customer_instance = stripe_handler.create_customer({
        "email": "test@test.com",
        "name": "Test User",
    })
    if customer_instance:
        updated_customer = stripe_handler.update_customer(customer_instance.id, {
            "email": "test2@test.com",
            "name": "Test User 2",
        })
        assert updated_customer is not None
        if updated_customer:
            assert updated_customer.email == "test2@test.com"
            assert updated_customer.name == "Test User 2"

def test_delete_customer(setUp):
    stripe_handler = setUp
    customer_instance = stripe_handler.create_customer({
        "email": "test@test.com",
        "name": "Test User",
    })
    if customer_instance:
        stripe_handler.delete_customer(customer_instance.id)
        deleted_customer = stripe_handler.get_customer(customer_instance.id)
        if isinstance(deleted_customer, stripe.Customer):
            assert deleted_customer.deleted == True

def test_customers_query(setUp):
    stripe_handler = setUp
    customers = stripe_handler.customers_query("email: 'test@test.com'")
    assert customers is not None
    if customers:
        assert isinstance(customers, dict)
        assert len(customers) > 0
        for customer in customers:
            assert isinstance(customer, stripe.Customer)

def test_create_customer_session(setUp):
    with app.app_context():
        stripe_handler = setUp
        customer_instance = stripe_handler.create_customer({
            "email": "test@test.com",
            "name": "Test User",
        })
        if customer_instance:
            session = stripe_handler.create_customer_session(customer_instance.id)
            assert session is not None
            if session:
                assert session.object == "customer_session"
                assert session.customer == customer_instance.id

def test_create_checkout_session(setUp):
    with app.app_context():
        stripe_handler = setUp
        customer_instance = stripe_handler.create_customer({
            "email": "test@test.com",
            "name": "Test User",
        })
    if customer_instance:
        session = stripe_handler.create_checkout_session(customer_instance.id, "https://example.com/success", "https://example.com/cancel")
        assert session is not None
        if session:
            if session.url:
                assert session.url.startswith("https://")
            assert session.id is not None
            assert session.object == "checkout.session"
            assert session.customer == customer_instance.id
            assert session.payment_method_types == ['card']
            assert session.mode == "payment"
            assert session.success_url == "https://example.com/success"
            assert session.cancel_url == "https://example.com/cancel"

def test_check_checkout_session(setUp):
    with app.app_context():
        # create a checkout session
        stripe_handler = setUp
        customer_instance = stripe_handler.create_customer({
            "email": "test@test.com",
            "name": "Test User",
        })
        session = stripe_handler.create_checkout_session(customer_instance.id, "https://example.com/success", "https://example.com/cancel")
        # check the session
        results = stripe_handler.check_checkout_session(session.id)
        assert results[0] == session
        assert results[1] == "open"

def test_handle_unsuccessful_payment(setUp):
    with app.app_context():
        stripe_handler = setUp
        customer_instance = stripe_handler.create_customer({
            "email": "test@test.com",
            "name": "Test User",
        })
        session = stripe_handler.create_checkout_session(customer_instance.id, "https://example.com/success", "https://example.com/cancel")
        # check the session
        results = stripe_handler.check_checkout_session(session.id)
        assert results[0] == session
        assert results[1] == "open"
        # handle the payment
        assert stripe_handler.handle_payment(session) == False 
        # check the session again
        results = stripe_handler.check_checkout_session(session.id)
        assert results[0] == session
        assert results[1] == "open"

        with patch("src.stripe_handler.StripeHandler.handle_payment") as mock_handle_payment:
            mock_handle_payment.return_value = True
            assert stripe_handler.handle_payment(session) == True
            mock_handle_payment.assert_called_once_with(session)
        
