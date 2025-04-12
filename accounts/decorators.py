# filepath: accounts/decorators.py
# filepath: accounts/decorators.py

from django.http import HttpResponseForbidden

def role_required(allowed_roles):
    """
    A decorator to restrict access to views based on the user's role.
    Allows access to users whose role is in the allowed_roles list.
    """
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return HttpResponseForbidden("You must be logged in to access this page.")
            if request.user.role not in allowed_roles:
                return HttpResponseForbidden("You do not have permission to access this page.")
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator