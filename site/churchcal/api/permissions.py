from rest_framework.permissions import BasePermission


class ReadOnly(BasePermission):

    def has_permission(self, request, view):
        return request.method == "GET"
