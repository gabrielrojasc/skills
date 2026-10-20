import requests
from django.conf import settings


def scopes_for(user) -> set[str]:
    response = requests.post(
        f"{settings.OPA_URL}/v1/data/zf/scopes",
        json={"input": {"user_id": user.pk, "company_id": user.company_id}},
        timeout=2,
    )
    response.raise_for_status()
    return set(response.json().get("result", []))
