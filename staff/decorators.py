from django.http import HttpResponseForbidden
from functools import wraps

def admin_staff_only(view_func):
    """
    Decorator to restrict access to staff users only.
    If user is not authenticated or not staff, returns 403 Forbidden.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.is_staff:
            return view_func(request, *args, **kwargs)
        return HttpResponseForbidden("You do not have permission to access this page.")
    return _wrapped_view
