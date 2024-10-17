from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from book.models import Book
from borrowing.models import Borrowing
from payment.models import Payment
from payment.serializers import PaymentSerializer, PaymentRetrieveSerializer

PAYMENT_URL = reverse("payment:payment-list")


def sample_book(**kwargs):
    defaults = {
        "title": "Test Book Title",
        "author": "Test Author",
        "cover": "SF",
        "inventory": 2,
        "daily_fee": 0.5,
    }
    defaults.update(**kwargs)
    return Book.objects.create(**defaults)


def sample_user(**kwargs):
    defaults = {
        "email": "some_user@mail.com",
        "password": "TestPassword12345",
    }
    defaults.update(**kwargs)
    return get_user_model().objects.create(**defaults)


def sample_borrowing(**kwargs):
    user = sample_user()
    book1 = sample_book(title="Book1")
    book2 = sample_book(title="Book2")

    borrowing = Borrowing.objects.create(
        expected_return_date="2024-10-17",
        user=user,
    )
    borrowing.book.add(book1)
    borrowing.book.add(book2)
    return borrowing


def detail_url(payment_id):
    return reverse("payment:payment-detail", args=[payment_id])


class UnauthenticatedPaymentAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        response = self.client.get(PAYMENT_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedPaymentAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = sample_user(email="user")
        self.client.force_authenticate(user=self.user)

    def test_payment_list(self):
        book1 = sample_book(title="Book1")
        book2 = sample_book(title="Book2")

        borrowing = Borrowing.objects.create(
            expected_return_date="2024-10-17",
            user=self.user,
        )
        borrowing.book.add(book1)
        borrowing.book.add(book2)
        borrowing.save()

        Payment.objects.create(type="PAYMENT", borrowing=borrowing)

        borrowing_other = sample_borrowing()
        Payment.objects.create(type="PAYMENT", borrowing=borrowing_other)

        response = self.client.get(PAYMENT_URL)

        payments = Payment.objects.filter(borrowing__user=self.user).order_by("id")
        serializer = PaymentSerializer(payments, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_retrieve_payment(self):
        book1 = sample_book(title="Book1")
        book2 = sample_book(title="Book2")

        borrowing = Borrowing.objects.create(
            expected_return_date="2024-10-17",
            user=self.user,
        )
        borrowing.book.add(book1)
        borrowing.book.add(book2)
        borrowing.save()

        payment = Payment.objects.create(type="PAYMENT", borrowing=borrowing)

        url = detail_url(payment.id)
        response = self.client.get(url)
        serializer = PaymentRetrieveSerializer(payment)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_retrieve_other_payment_not_found(self):
        borrowing_other = sample_borrowing()
        payment_other = Payment.objects.create(
            type="PAYMENT", borrowing=borrowing_other
        )

        url = detail_url(payment_other.id)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_put_payment_forbidden(self):
        book1 = sample_book(title="Book1")
        book2 = sample_book(title="Book2")

        borrowing = Borrowing.objects.create(
            expected_return_date="2024-10-17",
            user=self.user,
        )
        borrowing.book.add(book1)
        borrowing.book.add(book2)
        borrowing.save()

        payment = Payment.objects.create(type="PAYMENT", borrowing=borrowing)

        payload = {
            "type": "FINE",
        }

        url = detail_url(payment.id)

        response = self.client.put(url, payload)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_payment_forbidden(self):
        book1 = sample_book(title="Book1")
        book2 = sample_book(title="Book2")

        borrowing = Borrowing.objects.create(
            expected_return_date="2024-10-17",
            user=self.user,
        )
        borrowing.book.add(book1)
        borrowing.book.add(book2)
        borrowing.save()

        payment = Payment.objects.create(type="PAYMENT", borrowing=borrowing)

        url = detail_url(payment.id)

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class AdminPaymentAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = sample_user(email="admin@mail.com", is_staff=True)
        self.client.force_authenticate(user=self.user)

    def test_payment_list(self):
        book1 = sample_book(title="Book1")
        book2 = sample_book(title="Book2")

        borrowing = Borrowing.objects.create(
            expected_return_date="2024-10-17",
            user=self.user,
        )
        borrowing.book.add(book1)
        borrowing.book.add(book2)
        borrowing.save()

        Payment.objects.create(type="PAYMENT", borrowing=borrowing)

        borrowing_other = sample_borrowing()
        Payment.objects.create(type="PAYMENT", borrowing=borrowing_other)

        response = self.client.get(PAYMENT_URL)

        payments = Payment.objects.all()
        serializer = PaymentSerializer(payments, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_retrieve_payment(self):
        book1 = sample_book(title="Book1")
        book2 = sample_book(title="Book2")

        borrowing = Borrowing.objects.create(
            expected_return_date="2024-10-17",
            user=self.user,
        )
        borrowing.book.add(book1)
        borrowing.book.add(book2)
        borrowing.save()

        payment = Payment.objects.create(type="PAYMENT", borrowing=borrowing)

        url = detail_url(payment.id)
        response = self.client.get(url)
        serializer = PaymentRetrieveSerializer(payment)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_retrieve_payment_other_users(self):
        borrowing_other = sample_borrowing()
        payment_other = Payment.objects.create(
            type="PAYMENT", borrowing=borrowing_other
        )

        url = detail_url(payment_other.id)
        response = self.client.get(url)
        serializer = PaymentRetrieveSerializer(payment_other)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_put_payment_forbidden(self):
        book1 = sample_book(title="Book1")
        book2 = sample_book(title="Book2")

        borrowing = Borrowing.objects.create(
            expected_return_date="2024-10-17",
            user=self.user,
        )
        borrowing.book.add(book1)
        borrowing.book.add(book2)
        borrowing.save()

        payment = Payment.objects.create(type="PAYMENT", borrowing=borrowing)

        payload = {
            "type": "FINE",
        }

        url = detail_url(payment.id)

        response = self.client.put(url, payload)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_payment_forbidden(self):
        book1 = sample_book(title="Book1")
        book2 = sample_book(title="Book2")

        borrowing = Borrowing.objects.create(
            expected_return_date="2024-10-17",
            user=self.user,
        )
        borrowing.book.add(book1)
        borrowing.book.add(book2)
        borrowing.save()

        payment = Payment.objects.create(type="PAYMENT", borrowing=borrowing)

        url = detail_url(payment.id)

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
