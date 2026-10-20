# DRF conventions

- Use ViewSets for DRF endpoints and register them on the app's router.
- Start every `permission_classes` with `DEFAULT_GATES` from `core/permissions.py`.
- Gate a route on an OPA scope with `OPAScoped(<scope>)`, not with a check inside
  the view.
- Cover every endpoint with a test in `tests/`.
