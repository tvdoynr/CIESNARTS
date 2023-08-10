from functools import wraps

from django.core.exceptions import PermissionDenied

from accounts.models import Profile


def user_has_role(*roles):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            profile = Profile.objects.get(user=request.user)
            if profile.user_type in roles:
                return view_func(request, *args, **kwargs)
            else:
                raise PermissionDenied

        return _wrapped_view

    return decorator