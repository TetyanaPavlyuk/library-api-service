from django.contrib.auth import get_user_model
from django.urls import reverse

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from user.models import User
from user.serializers import UserSerializer

USER_URL = "http://127.0.0.1:8000/api/library/users/"
USER_URL_LIST = "http://127.0.0.1:8000/api/library/users/users/"


user_payload = {
    "email": "test_user@mail.com",
    "first_name": "test_first_name",
    "last_name": "test_last_name",
    "password": "TestPassword1234",
}


def sample_user(**kwargs):
    defaults = user_payload.copy()
    defaults.update(**kwargs)
    return User.objects.create(**defaults)


def detail_url(user_id):
    return reverse("user:user-detail", args=[user_id])


class UnauthenticatedUserApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_non_auth_can_register(self):
        response = self.client.post(USER_URL, data=user_payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_auth_required(self):
        response = self.client.get(USER_URL_LIST)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedUserApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(**user_payload)
        self.client.force_authenticate(self.user)

    def test_list_users_forbidden(self):
        sample_user(email="user1@mail.com")
        sample_user(email="user2@mail.com")

        response = self.client.get(USER_URL_LIST)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class AdminUserApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(is_staff=True, **user_payload)
        self.client.force_authenticate(self.user)

    def test_list_users(self):
        sample_user(email="user1@mail.com")
        sample_user(email="user2@mail.com")

        response = self.client.get(USER_URL_LIST)

        users = User.objects.order_by("id")
        serializer = UserSerializer(users, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_put_user(self):
        payload = {
            "email": "other_user@mail.com",
            "first_name": "other_first_name",
            "last_name": "other_last_name",
        }

        user = sample_user(email="some_user@mail.com")
        url = detail_url(user.id)

        response = self.client.put(url, payload)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_user_not_allowed(self):
        user = sample_user(email="some@mail.com")
        url = detail_url(user.id)

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
