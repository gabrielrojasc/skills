from core import opa_client


def has_scope(request, scope: str) -> bool:
    return scope in opa_client.scopes_for(request.user)
