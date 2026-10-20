from django.conf import settings
from flagsmith import Flagsmith
from flagsmith.exceptions import FlagsmithClientError as FlagsmithError

_client = Flagsmith(environment_key=settings.FLAGSMITH_ENVIRONMENT_KEY)

__all__ = ["FlagsmithError", "company_flags"]


def company_flags(company_id):
    return _client.get_identity_flags(identifier=f"company-{company_id}")
