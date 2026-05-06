"""
Supabase JWT verification for Flask API routes.
"""
from __future__ import annotations

import functools
import logging
from typing import Any, Dict, Optional

import jwt
from jwt import PyJWKClient
from flask import g, jsonify, request

from backend.config import Config

logger = logging.getLogger(__name__)
_jwks_client: Optional[PyJWKClient] = None


def _get_jwks_client() -> Optional[PyJWKClient]:
    """Build cached JWKS client for Supabase asymmetric JWT verification."""
    global _jwks_client
    jwks_url = getattr(Config, 'SUPABASE_JWKS_URL', '')
    if not jwks_url:
        return None
    if _jwks_client is None:
        _jwks_client = PyJWKClient(jwks_url)
    return _jwks_client


def verify_supabase_jwt(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify a Supabase-issued access token.
    Supports asymmetric (JWKS/ES256) and legacy symmetric (HS256) verification.
    """
    if not token:
        return None
    try:
        payload = None
        jwks_client = _get_jwks_client()
        if jwks_client:
            signing_key = jwks_client.get_signing_key_from_jwt(token)
            if getattr(Config, 'SUPABASE_JWT_KID', '') and signing_key.key_id != Config.SUPABASE_JWT_KID:
                logger.debug('JWT kid mismatch: expected=%s got=%s', Config.SUPABASE_JWT_KID, signing_key.key_id)
                return None
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=['ES256', 'RS256'],
                options={'verify_aud': False},
            )
        elif getattr(Config, 'SUPABASE_JWT_SECRET', ''):
            payload = jwt.decode(
                token,
                Config.SUPABASE_JWT_SECRET,
                algorithms=['HS256'],
                options={'verify_aud': False},
            )
        else:
            return None

        sub = payload.get('sub')
        if not sub:
            return None
        return {'sub': str(sub), 'email': payload.get('email')}
    except jwt.PyJWTError as exc:
        logger.debug('JWT verification failed: %s', exc)
        return None


def attach_current_user() -> None:
    """Resolve Bearer token into g.user (optional)."""
    g.user = None
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return
    token = auth_header[7:].strip()
    user = verify_supabase_jwt(token)
    if user:
        g.user = user


def login_required(fn):
    """Require a valid Supabase JWT when REQUIRE_AUTH_FOR_SAVES is True (g.user set by before_request)."""

    @functools.wraps(fn)
    def wrapped(*args, **kwargs):
        if not getattr(Config, 'REQUIRE_AUTH_FOR_SAVES', True):
            return fn(*args, **kwargs)
        if not getattr(g, 'user', None):
            return jsonify({'error': 'Authentication required'}), 401
        return fn(*args, **kwargs)

    return wrapped


def current_user_id() -> Optional[str]:
    """Return authenticated user's UUID string or None."""
    try:
        user = getattr(g, 'user', None)
    except RuntimeError:
        # Accessed outside request/application context (e.g., worker thread).
        return None
    if not user:
        return None
    return user.get('sub')
