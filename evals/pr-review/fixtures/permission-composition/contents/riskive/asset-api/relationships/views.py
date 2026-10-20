from rest_framework import mixins, status, viewsets
from rest_framework.permissions import BasePermission
from rest_framework.response import Response

from core.permissions import DEFAULT_GATES, OPAScoped
from relationships.models import Relationship, RelationshipType
from relationships.serializers import (
    RelationshipCreateSerializer,
    RelationshipSerializer,
    RelationshipTypeSerializer,
)
from relationships.services import (
    MANAGE_RELATIONSHIPS_SCOPE,
    RelationshipConflictError,
    can_view_relationships,
    create_relationship,
)

WRITE_METHODS = ("POST", "PUT", "PATCH", "DELETE")


class CanViewRelationships(BasePermission):
    def has_permission(self, request, view):
        return can_view_relationships(request)


class ManageOnWrite(OPAScoped(MANAGE_RELATIONSHIPS_SCOPE)):
    def has_permission(self, request, view):
        return request.method not in WRITE_METHODS or super().has_permission(request, view)


class RelationshipTypeViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    permission_classes = [*DEFAULT_GATES, CanViewRelationships]
    serializer_class = RelationshipTypeSerializer
    pagination_class = None
    queryset = RelationshipType.objects.all()


class RelationshipViewSet(
    mixins.ListModelMixin, mixins.CreateModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet
):
    permission_classes = [*DEFAULT_GATES, CanViewRelationships, ManageOnWrite]
    serializer_class = RelationshipSerializer

    def get_queryset(self):
        return Relationship.objects.filter(company=self.request.user.company)

    def create(self, request, *args, **kwargs):
        serializer = RelationshipCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        try:
            data = serializer.validated_data
            relationship = create_relationship(request.user.company, data["parent"], data["child"], data["type"])
        except RelationshipConflictError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)
        return Response(RelationshipSerializer(relationship).data, status=status.HTTP_201_CREATED)
