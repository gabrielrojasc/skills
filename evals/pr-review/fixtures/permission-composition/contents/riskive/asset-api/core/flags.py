from typing import NewType

from core import flagsmith

FlagName = NewType("FlagName", str)


def is_feature_enabled(request, flag: FlagName) -> bool:
    user = getattr(request, "user", None)
    if user is None or not user.is_authenticated:
        return False
    try:
        return flagsmith.company_flags(user.company_id).is_feature_enabled(flag)
    except flagsmith.FlagsmithError:
        return False
