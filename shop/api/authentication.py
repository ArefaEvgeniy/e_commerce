import jwt
from django.contrib.auth import get_user_model
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.conf import settings
from django.core.cache import cache


User = get_user_model()
JWT_SETTINGS = getattr(settings, 'SIMPLE_JWT', {})


class EcommerceJWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return None

        try:
            token_type, token = auth_header.split()
            if token_type.title() not in JWT_SETTINGS.get('AUTH_HEADER_TYPES', ['Bearer']):
                raise AuthenticationFailed('Invalid token type')
        except ValueError:
            raise AuthenticationFailed('Invalid authorization header format')

        try:
            payload = jwt.decode(token, settings.SECRET_KEY,  algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Token has expired')
        except jwt.InvalidTokenError:
            raise AuthenticationFailed('Invalid token')

        if payload.get('type') != 'access':
            raise AuthenticationFailed('Invalid token type')

        try:
            user_payload = {key: payload.get(key) for key in JWT_SETTINGS.get('USER_ID_FIELDS', ['id'])}
            user = User.objects.get(**user_payload)
            if not user.is_active:
                raise AuthenticationFailed('User is inactive')
        except User.DoesNotExist:
            raise AuthenticationFailed('User not found')

        return user, token
