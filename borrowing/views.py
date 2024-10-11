from datetime import date

from django.db import transaction
from django.shortcuts import redirect
from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from borrowing.models import Borrowing
from borrowing.permissions import AdminOrIsAuthenticatedCreateAndReadOnly
from borrowing.serializers import (
    BorrowingAdminSerializer,
    BorrowingUserSerializer,
    BorrowingListAdminSerializer,
    BorrowingListUserSerializer,
    BorrowingRetrieveSerializer,
)


class BorrowingPagination(PageNumberPagination):
    page_size = 10
    max_page_size = 50


class BorrowingViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    GenericViewSet,
):
    queryset = Borrowing.objects.all()
    permission_classes = (AdminOrIsAuthenticatedCreateAndReadOnly,)
    pagination_class = BorrowingPagination

    def get_queryset(self):
        queryset = self.queryset
        is_active = self.request.query_params.get("is_active")
        user_id = self.request.query_params.get("user_id")

        if self.action == "list":
            queryset = queryset.select_related().prefetch_related("book")
            if is_active == "true" or is_active == "True":
                queryset = queryset.filter(actual_return_date__isnull=True)
            elif is_active == "false" or is_active == "False":
                queryset = queryset.filter(actual_return_date__isnull=False)

        user = self.request.user
        if user.is_staff:
            if user_id is not None:
                user_id_list = user_id.split(",")
                queryset = queryset.filter(user_id__in=user_id_list)
            return queryset
        return queryset.filter(user=user)

    def get_serializer_class(self):
        user = self.request.user
        if self.action == "list" and user.is_staff:
            return BorrowingListAdminSerializer
        elif self.action == "list" and not user.is_staff:
            return BorrowingListUserSerializer
        elif self.action == "retrieve":
            return BorrowingRetrieveSerializer

        if self.request.user.is_staff:
            return BorrowingAdminSerializer
        else:
            return BorrowingUserSerializer

    def perform_create(self, serializer):
        if self.request.user.is_staff:
            serializer.save()
        else:
            serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            redirect_url = "http://127.0.0.1:8000/api/library/payments/create_payment"
            return Response(status=status.HTTP_302_FOUND, headers={"Location": redirect_url})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(
        methods=["POST"],
        detail=True,
        url_path="return",
        permission_classes=(IsAdminUser, )
    )
    def return_book(self, request, pk=None):
        borrowing = self.get_object()
        return_date = date.today()

        if borrowing.actual_return_date is not None:
            return Response(
                {"detail": "Books have already been returned."},
                status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            borrowing.actual_return_date = return_date
            borrowing.save()
            for book in borrowing.book.all():
                book.inventory += 1
                book.save()

        return Response(
            {"detail": f"Books {[book.title for book in borrowing.book.all()]} have been returned."},
            status=status.HTTP_200_OK
        )
