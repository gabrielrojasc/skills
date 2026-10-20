from core.flags import is_feature_enabled
from core.opa import has_scope
from relationships.feature_flags import FAMILY_MAPPING_FLAG
from relationships.models import Relationship

VIEW_RELATIONSHIPS_SCOPE = "entity:view_relationships"
MANAGE_RELATIONSHIPS_SCOPE = "entity:manage_relationships"


class RelationshipConflictError(Exception):
    pass


def can_view_relationships(request) -> bool:
    """The view scope, or the family-mapping flag that stands in for it."""
    if request is None:
        return False
    if has_scope(request, VIEW_RELATIONSHIPS_SCOPE):
        return True
    return is_feature_enabled(request, FAMILY_MAPPING_FLAG)


def create_relationship(company, parent, child, relationship_type):
    if Relationship.objects.filter(company=company, parent=parent, child=child).exists():
        raise RelationshipConflictError(f"{parent.pk} -> {child.pk} already exists")
    return Relationship.objects.create(company=company, parent=parent, child=child, type=relationship_type)
