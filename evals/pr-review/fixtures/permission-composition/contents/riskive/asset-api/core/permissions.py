from rest_framework.permissions import BasePermission, IsAuthenticated

from core.flags import FlagName, is_feature_enabled
from core.opa import has_scope


class UserEnabledPermission(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_active


DEFAULT_GATES = [IsAuthenticated, UserEnabledPermission]


def OPAScoped(scope: str):
    class _OPAScoped(BasePermission):
        def has_permission(self, request, view):
            return has_scope(request, scope)

    _OPAScoped.__name__ = f"OPAScoped({scope})"
    return _OPAScoped


def RequireFeatureFlag(flag: FlagName):
    class _RequireFeatureFlag(BasePermission):
        def has_permission(self, request, view):
            return is_feature_enabled(request, flag)

    _RequireFeatureFlag.__name__ = f"RequireFeatureFlag({flag})"
    return _RequireFeatureFlag
