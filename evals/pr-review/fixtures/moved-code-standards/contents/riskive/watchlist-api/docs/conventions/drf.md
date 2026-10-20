# DRF conventions

- Use ViewSets for DRF endpoints. Do not introduce standalone `APIView` or generic view subclasses.
- Register every ViewSet on the app's router in `urls.py`.
- Scope every queryset to `request.user.organization`.
- Cover every endpoint with a test in `tests/`.
