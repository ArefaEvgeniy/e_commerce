from datetime import datetime, timedelta, timezone

import jwt
from django.conf import settings


JWT_SETTINGS = getattr(settings, 'SIMPLE_JWT', {})
ACCESS_TOKEN_LIFETIME = JWT_SETTINGS.get('ACCESS_TOKEN_LIFETIME', timedelta(minutes=2))
REFRESH_TOKEN_LIFETIME = JWT_SETTINGS.get('REFRESH_TOKEN_LIFETIME', timedelta(minutes=4))


def populate_user_payload(payload, user):
    for field in JWT_SETTINGS.get('USER_ID_FIELDS', ['id']):
        payload[field] = getattr(user, field, None)

    return payload


def create_access_token(user):
    token_payload = {
        'exp': datetime.now(tz=timezone.utc) + ACCESS_TOKEN_LIFETIME,
        'iat': datetime.now(tz=timezone.utc),
        'type': 'access'
    }
    return jwt.encode(
        populate_user_payload(token_payload, user),
        settings.SECRET_KEY,
        algorithm='HS256'
    )


def create_refresh_token(user):
    token_payload = {
        'exp': datetime.now(tz=timezone.utc) + REFRESH_TOKEN_LIFETIME,
        'iat': datetime.now(tz=timezone.utc),
        'type': 'refresh'
    }
    return jwt.encode(
        populate_user_payload(token_payload, user),
        settings.SECRET_KEY,
        algorithm='HS256'
    )
