from django.conf import settings
from django.http import HttpResponse

import functools
import jwt

def authorized_only(model, allowed_roles):
    def decorator_authorized_only(func):
        @functools.wraps(func)
        def wrapper_authorized_only(request, *args, **kwargs):

            if 'jwt' not in request.COOKIES:
                return HttpResponse('Unauthorized', status=401)

            decoded = jwt.decode(request.COOKIES['jwt'], settings.SECRET_KEY, algorithms=[settings.JWT_ALGO])

            try:
                emp = model.objects.get(public_id=decoded['id'])
            except model.DoesNotExist:
                return HttpResponse('[AUTH] account not found', status=404)

            authorized = False
            for role in emp.roles:
            # for role in decoded.get('roles',[]):
                if role in allowed_roles:
                    authorized = True
                    break

            if not authorized:
                return HttpResponse('Unauthorized', status=401)

            return func(request, *args, **kwargs)

        return wrapper_authorized_only

    return decorator_authorized_only
