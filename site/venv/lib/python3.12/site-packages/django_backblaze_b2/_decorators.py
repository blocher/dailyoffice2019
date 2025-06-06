from functools import wraps

from django.http import HttpRequest, HttpResponse
from django.utils.translation import gettext_lazy as _


def _requires_login(requires_staff=False):
    """
    Decorator for views that checks that the user passes the given test,
    redirecting to the log-in page if necessary. The test should be a callable
    that takes the user object and returns True if the user passes.
    """

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request: HttpRequest, *args, **kwargs):
            from django.contrib.auth.views import redirect_to_login  # delay import in case custom user model

            if request.user.is_anonymous:
                return redirect_to_login(request.get_full_path())
            if not request.user.is_active or (requires_staff and not request.user.is_staff):
                return HttpResponse(_("Unauthorized"), status=401)
            return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorator
