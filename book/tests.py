from django.contrib.auth import get_user_model
from django.urls import reverse

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from book.models import Book
from book.serializers import BookSerializer

BOOK_URL = reverse("book:book-list")


book_payload = {
    "title": "Test Book Title",
    "author": "Test Author",
    "cover": "SF",
    "inventory": 3,
    "daily_fee": 0.5,
}


def sample_book(**kwargs):
    defaults = book_payload.copy()
    defaults.update(**kwargs)
    return Book.objects.create(**defaults)


def detail_url(book_id):
    return reverse("book:book-detail", args=[book_id])


class UnauthenticatedBookApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_list_books(self):
        sample_book(title="Test Book 1")
        sample_book(title="Test Book 2")

        response = self.client.get(BOOK_URL)

        books = Book.objects.order_by("id")
        serializer = BookSerializer(books, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_retrieve_book_detail(self):
        book = sample_book()

        url = detail_url(book.id)
        response = self.client.get(url)

        serializer = BookSerializer(book)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_create_book_unauthorized(self):
        payload = book_payload.copy()
        response = self.client.post(BOOK_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedBookApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "user@mail.com",
            "TestPassword12345",
        )
        self.client.force_authenticate(self.user)

    def test_list_books(self):
        sample_book(title="Test Book 1")
        sample_book(title="Test Book 2")

        response = self.client.get(BOOK_URL)

        books = Book.objects.order_by("id")
        serializer = BookSerializer(books, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_retrieve_book_detail(self):
        book = sample_book()

        url = detail_url(book.id)
        response = self.client.get(url)

        serializer = BookSerializer(book)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_create_book_forbidden(self):
        payload = book_payload.copy()
        response = self.client.post(BOOK_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_book_forbidden(self):
        book = sample_book()
        url = detail_url(book.id)

        response = self.client.delete(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN
        )


class AdminBookApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "admin@mail.com", "TestPassword12345", is_staff=True
        )
        self.client.force_authenticate(self.user)

    def test_create_book(self):
        payload = book_payload.copy()
        response = self.client.post(BOOK_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_put_book(self):
        payload = {
            "title": "Some Other Title",
            "author": "Some Other Author",
            "cover": "HR",
            "inventory": 3,
            "daily_fee": 0.75,
        }

        book = sample_book()
        url = detail_url(book.id)

        response = self.client.put(url, payload)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

    def test_delete_book(self):
        book = sample_book()
        url = detail_url(book.id)

        response = self.client.delete(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT
        )
