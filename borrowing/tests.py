from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from book.models import Book
from borrowing.models import Borrowing
from borrowing.serializers import (
    BorrowingListUserSerializer,
    BorrowingListAdminSerializer,
    BorrowingRetrieveSerializer,
    BorrowingUserSerializer,
    BorrowingAdminSerializer,
)

BORROWING_URL = reverse("borrowing:borrowing-list")


def sample_book(**kwargs):
    defaults = {
        "title": "Test Book Title",
        "author": "Test Author",
        "cover": "SF",
        "inventory": 3,
        "daily_fee": 0.5,
    }
    defaults.update(**kwargs)
    return Book.objects.create(**defaults)


def sample_user(**kwargs):
    defaults = {
        "email": "user@mail.com",
        "password": "TestPassword12345",
    }
    defaults.update(**kwargs)
    return get_user_model().objects.create(**defaults)


def detail_url(borrowing_id):
    return reverse("borrowing:borrowing-detail", args=[borrowing_id])


class UnauthenticatedBorrowingAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        response = self.client.get(BORROWING_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedBorrowingAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = sample_user()
        self.client.force_authenticate(user=self.user)

    def test_borrowing_list(self):
        book1 = sample_book(title="Book1")
        book2 = sample_book(title="Book2")
        book3 = sample_book(title="Book3")

        other_user = sample_user(email="other_user@mail.com")

        borrowing1 = Borrowing.objects.create(
            expected_return_date="2024-10-17",
            user=self.user,
        )
        borrowing1.book.add(book1)
        borrowing1.book.add(book2)

        borrowing2 = Borrowing.objects.create(
            expected_return_date="2024-10-17",
            user=other_user,
        )
        borrowing2.book.add(book3)

        response = self.client.get(BORROWING_URL)

        borrowings = Borrowing.objects.filter(user=self.user).order_by("id")
        serializer = BorrowingListUserSerializer(borrowings, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"], serializer.data)

    def test_filter_borrowing_by_is_active(self):
        book1 = sample_book(title="Book1")
        book2 = sample_book(title="Book2")
        book3 = sample_book(title="Book3")

        borrowing1 = Borrowing.objects.create(
            expected_return_date="2024-10-17",
            user=self.user,
        )
        borrowing1.book.add(book1)
        borrowing1.book.add(book2)

        borrowing2 = Borrowing.objects.create(
            expected_return_date="2024-10-17",
            user=self.user,
        )
        borrowing2.book.add(book3)
        borrowing2.actual_return_date = "2024-10-17"
        borrowing2.save()

        response = self.client.get(BORROWING_URL, {"is_active": "True"})

        serializer_in = BorrowingListUserSerializer(borrowing1)
        serializer_out = BorrowingListUserSerializer(borrowing2)

        self.assertIn(serializer_in.data, response.data["results"])
        self.assertNotIn(serializer_out.data, response.data["results"])

    def test_retrieve_borrowing(self):
        book1 = sample_book(title="Book1")
        book2 = sample_book(title="Book2")

        borrowing = Borrowing.objects.create(
            expected_return_date="2024-10-17",
            user=self.user,
        )
        borrowing.book.add(book1)
        borrowing.book.add(book2)

        url = detail_url(borrowing.id)
        response = self.client.get(url)
        serializer = BorrowingRetrieveSerializer(borrowing)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_retrieve_other_borrowing_not_found(self):
        book = sample_book()

        other_user = sample_user(email="other_user@mail.com")
        borrowing_other_user = Borrowing.objects.create(
            expected_return_date="2024-10-17",
            user=other_user,
        )
        borrowing_other_user.book.add(book)

        url = detail_url(borrowing_other_user.id)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_borrowing(self):
        book1 = sample_book(title="Book1")
        book2 = sample_book(title="Book2")

        payload = {
            "expected_return_date": "2024-10-17",
            "book": [book1.id, book2.id],
            "user": self.user.id,
        }

        response = self.client.post(BORROWING_URL, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertIn("Location", response.headers)

        borrowing_1 = Borrowing.objects.get(
            expected_return_date=payload["expected_return_date"],
            user=payload["user"],
        )
        serializer = BorrowingUserSerializer(borrowing_1)

        for book_id in payload["book"]:
            self.assertIn(book_id, serializer.data["book"])

        self.assertEqual(
            payload["expected_return_date"],
            serializer.data["expected_return_date"],
        )

    def test_put_borrowing_forbidden(self):
        book1 = sample_book(title="Book1")
        book2 = sample_book(title="Book2")

        borrowing = Borrowing.objects.create(
            expected_return_date="2024-10-17",
            user=self.user,
        )
        borrowing.book.add(book1)
        borrowing.book.add(book2)

        payload = {
            "book": [book1.id],
        }

        url = detail_url(borrowing.id)

        response = self.client.put(url, payload)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_borrowing_forbidden(self):
        book1 = sample_book(title="Book1")
        book2 = sample_book(title="Book2")

        borrowing = Borrowing.objects.create(
            expected_return_date="2024-10-17",
            user=self.user,
        )
        borrowing.book.add(book1)
        borrowing.book.add(book2)

        url = detail_url(borrowing.id)

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class AdminBorrowingAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = sample_user(is_staff=True)
        self.client.force_authenticate(user=self.user)

    def test_borrowing_list(self):
        book1 = sample_book(title="Book1")
        book2 = sample_book(title="Book2")
        book3 = sample_book(title="Book3")

        other_user = sample_user(email="other_user@mail.com")

        borrowing1 = Borrowing.objects.create(
            expected_return_date="2024-10-17",
            user=self.user,
        )
        borrowing1.book.add(book1)
        borrowing1.book.add(book2)

        borrowing2 = Borrowing.objects.create(
            expected_return_date="2024-10-17",
            user=other_user,
        )
        borrowing2.book.add(book3)

        response = self.client.get(BORROWING_URL)

        borrowings = Borrowing.objects.all()
        serializer = BorrowingListAdminSerializer(borrowings, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"], serializer.data)

    def test_filter_borrowing_by_is_active(self):
        book1 = sample_book(title="Book1")
        book2 = sample_book(title="Book2")
        book3 = sample_book(title="Book3")

        other_user = sample_user(email="other_user@mail.com")

        borrowing1 = Borrowing.objects.create(
            expected_return_date="2024-10-17",
            user=self.user,
        )
        borrowing1.book.add(book1)
        borrowing1.book.add(book2)

        borrowing2 = Borrowing.objects.create(
            expected_return_date="2024-10-17",
            user=other_user,
        )
        borrowing2.book.add(book3)
        borrowing2.actual_return_date = "2024-10-17"
        borrowing2.save()

        response = self.client.get(BORROWING_URL, {"is_active": "True"})

        serializer_in = BorrowingListAdminSerializer(borrowing1)
        serializer_out = BorrowingListAdminSerializer(borrowing2)

        self.assertIn(serializer_in.data, response.data["results"])
        self.assertNotIn(serializer_out.data, response.data["results"])

    def test_filter_borrowing_by_user_id(self):
        book1 = sample_book(title="Book1")
        book2 = sample_book(title="Book2")
        book3 = sample_book(title="Book3")
        book4 = sample_book(title="Book4")

        user1 = sample_user(email="user1@mail.com")
        user2 = sample_user(email="user2@mail.com")

        borrowing = Borrowing.objects.create(
            expected_return_date="2024-10-17",
            user=self.user,
        )
        borrowing.book.add(book1)
        borrowing.book.add(book2)

        borrowing1 = Borrowing.objects.create(
            expected_return_date="2024-10-17",
            user=user1,
        )
        borrowing1.book.add(book3)

        borrowing2 = Borrowing.objects.create(
            expected_return_date="2024-10-17",
            user=user2,
        )
        borrowing2.book.add(book4)

        response = self.client.get(BORROWING_URL, {"user_id": [self.user.id, user1.id]})

        serializer_in = BorrowingListAdminSerializer(borrowing)
        serializer_in1 = BorrowingListAdminSerializer(borrowing1)
        serializer_out2 = BorrowingListAdminSerializer(borrowing2)

        self.assertIn(serializer_in.data, response.data["results"])
        self.assertIn(serializer_in1.data, response.data["results"])
        self.assertNotIn(serializer_out2.data, response.data["results"])

    def test_retrieve_borrowing(self):
        book1 = sample_book(title="Book1")
        book2 = sample_book(title="Book2")

        borrowing = Borrowing.objects.create(
            expected_return_date="2024-10-17",
            user=self.user,
        )
        borrowing.book.add(book1)
        borrowing.book.add(book2)

        url = detail_url(borrowing.id)
        response = self.client.get(url)
        serializer = BorrowingRetrieveSerializer(borrowing)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_retrieve_borrowing_other_user(self):
        book = sample_book()

        other_user = sample_user(email="other_user@mail.com")
        borrowing_other_user = Borrowing.objects.create(
            expected_return_date="2024-10-17",
            user=other_user,
        )
        borrowing_other_user.book.add(book)

        url = detail_url(borrowing_other_user.id)
        response = self.client.get(url)
        serializer = BorrowingRetrieveSerializer(borrowing_other_user)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_create_borrowing(self):
        book1 = sample_book(title="Book1")
        book2 = sample_book(title="Book2")

        payload = {
            "expected_return_date": "2024-10-17",
            "book": [book1.id, book2.id],
            "user": self.user.id,
        }

        response = self.client.post(BORROWING_URL, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertIn("Location", response.headers)

        borrowing_1 = Borrowing.objects.get(
            expected_return_date=payload["expected_return_date"],
            user=payload["user"],
        )
        serializer = BorrowingAdminSerializer(borrowing_1)

        for book_id in payload["book"]:
            self.assertIn(book_id, serializer.data["book"])

        self.assertEqual(
            payload["expected_return_date"],
            serializer.data["expected_return_date"],
        )

    def test_put_borrowing_not_allowed(self):
        book1 = sample_book(title="Book1")
        book2 = sample_book(title="Book2")

        borrowing = Borrowing.objects.create(
            expected_return_date="2024-10-17",
            user=self.user,
        )
        borrowing.book.add(book1)
        borrowing.book.add(book2)

        payload = {
            "book": [book1.id],
        }

        url = detail_url(borrowing.id)

        response = self.client.put(url, payload)

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_delete_borrowing_not_allowed(self):
        book1 = sample_book(title="Book1")
        book2 = sample_book(title="Book2")

        borrowing = Borrowing.objects.create(
            expected_return_date="2024-10-17",
            user=self.user,
        )
        borrowing.book.add(book1)
        borrowing.book.add(book2)

        url = detail_url(borrowing.id)

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
