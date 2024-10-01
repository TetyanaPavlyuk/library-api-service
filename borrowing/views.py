from rest_framework import mixins
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

    def get_queryset(self):
        queryset = self.queryset
        if self.action == "list":
            queryset = queryset.select_related().prefetch_related("book")

        user = self.request.user
        if user.is_staff:
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
