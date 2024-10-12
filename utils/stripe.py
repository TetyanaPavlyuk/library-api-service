import stripe

from borrowing.models import Borrowing


def create_stripe_session_for_payment(borrowing: Borrowing) -> stripe.checkout.Session:
    session = stripe.checkout.Session.create(
        line_items=[
            {
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": f"Payment for {borrowing.books_in_borrowing}",
                    },
                    "unit_amount": int(borrowing.calculate_payment_amount() * 100),
                },
                "quantity": 1,
            }
        ],
        mode="payment",
        success_url="http://127.0.0.1:8000/api/library/payments/success?session_id={CHECKOUT_SESSION_ID}",
        cancel_url="http://127.0.0.1:8000/api/library/payments/cancel",
    )

    return session


def create_stripe_session_for_fine(borrowing: Borrowing) -> stripe.checkout.Session:
    session = stripe.checkout.Session.create(
        line_items=[
            {
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": f"Fine for {borrowing.books_in_borrowing}",
                    },
                    "unit_amount": int(borrowing.calculate_fine_amount() * 100),
                },
                "quantity": 1,
            }
        ],
        mode="payment",
        success_url="http://127.0.0.1:8000/api/library/payments/success?session_id={CHECKOUT_SESSION_ID}",
        cancel_url="http://127.0.0.1:8000/api/library/payments/cancel",
    )

    return session
