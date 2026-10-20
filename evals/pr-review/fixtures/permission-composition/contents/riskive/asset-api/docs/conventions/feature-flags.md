# Feature flags

Declare each flag as a `FlagName` in its app's `feature_flags.py`.

When an endpoint needs a flag, add `RequireFeatureFlag(<flag>)` from
`core/permissions.py` to the existing permission stack. DRF permissions compose
with `&` and `|`, so a flag that grants access on its own, without the usual
scope, is `OPAScoped(<scope>) | RequireFeatureFlag(<flag>)`. For new behavior
inside an existing endpoint, check `is_feature_enabled(request, <flag>)` in that
branch so flag-off keeps the existing response.

Flags evaluate for the request user's company and fail closed when Flagsmith
can't be reached.
