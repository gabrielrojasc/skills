from rest_framework.routers import DefaultRouter

from relationships.views import RelationshipTypeViewSet, RelationshipViewSet

router = DefaultRouter()
router.register("relationship-types", RelationshipTypeViewSet, basename="relationship-type")
router.register("relationships", RelationshipViewSet, basename="relationship")

urlpatterns = router.urls
