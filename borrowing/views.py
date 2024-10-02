from rest_framework import mixins
from rest_framework.pagination import PageNumberPagination
from rest_framework.viewsets import GenericViewSet

from borrowing.models import Borrowing
from borrowing.permissions import AdminOrIsAuthenticatedCreateAndReadOnly
from borrowing.serializers import (
    BorrowingAdminSerializer,
    BorrowingUserSerializer,
    BorrowingListAdminSerializer,
    BorrowingListUserSerializer,
    BorrowingRetrieveSerializer,
    BorrowingUpdateSerializer
)


class BorrowingPagination(PageNumberPagination):
    page_size = 10
    max_page_size = 50


class BorrowingViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    GenericViewSet
):
    queryset = Borrowing.objects.all()
    permission_classes = (AdminOrIsAuthenticatedCreateAndReadOnly, )
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
        elif self.action == "update":
            return BorrowingUpdateSerializer

        if self.request.user.is_staff:
            return BorrowingAdminSerializer
        else:
            return BorrowingUserSerializer

    def perform_create(self, serializer):
        if self.request.user.is_staff:
            serializer.save()
        else:
            serializer.save(user=self.request.user)
