from rest_framework import permissions


class CanNotEditAndDeletePayments(permissions.BasePermission):
    def has_permission(self, request, view):
        return view.action not in ["update", "partial_update", "destroy"]
