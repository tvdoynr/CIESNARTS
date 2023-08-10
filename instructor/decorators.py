from django.core.exceptions import PermissionDenied

from accounts.models import Profile


def user_is_instructor(function):
    def wrap(request, *args, **kwargs):
        profile = Profile.objects.get(user=request.user)
        if profile.user_type == 'instructor':
            return function(request, *args, **kwargs)
        else:
            raise PermissionDenied

    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap