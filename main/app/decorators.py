from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.core.exceptions import PermissionDenied

def role_required(allowed_roles):
    """Пускает только авторизованных пользователей с ролью из allowed_roles.
       Анонимных отправляет на вход."""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, "Требуется вход в систему.")
                return redirect('signin')
            profile, _ = request.user.profile.__class__.objects.get_or_create(user=request.user)
            role = profile.role
            if role == 'admin' or role in allowed_roles:
                return view_func(request, *args, **kwargs)
            messages.error(request, "У вас нет прав для доступа к этой странице.")
            raise PermissionDenied
        return wrapper
    return decorator