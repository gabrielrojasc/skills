from functools import wraps

from django.http import JsonResponse


def staff_required(view):
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_staff:
            return JsonResponse({"error": "forbidden"}, status=403)
        return view(request, *args, **kwargs)

    return wrapper
