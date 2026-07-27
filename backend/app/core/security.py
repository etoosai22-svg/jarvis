"""요청자 식별. Phase 7(OAuth) 전까지는 로컬 개발 사용자로 동작한다."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Annotated, Any

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient

from app.core.config import Settings, get_settings

logger = logging.getLogger(__name__)

# auto_error=False: 인증이 꺼진 로컬 환경에서 헤더가 없어도 통과시킨다.
bearer_scheme = HTTPBearer(auto_error=False)

_jwk_clients: dict[str, PyJWKClient] = {}


@dataclass(frozen=True)
class CurrentUser:
    id: str
    claims: dict[str, Any]

    @property
    def is_dev_user(self) -> bool:
        return not self.claims


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def _jwk_client(jwks_url: str) -> PyJWKClient:
    # PyJWKClient는 키를 캐시하므로 URL당 하나만 만들어 재사용한다.
    client = _jwk_clients.get(jwks_url)
    if client is None:
        client = PyJWKClient(jwks_url, cache_keys=True)
        _jwk_clients[jwks_url] = client
    return client


def _decode_token(token: str, settings: Settings) -> dict[str, Any]:
    jwks_url = settings.resolved_jwks_url
    if not jwks_url:
        raise _unauthorized("인증이 필요하지만 OAuth 발급자가 설정되지 않았습니다.")

    try:
        signing_key = _jwk_client(jwks_url).get_signing_key_from_jwt(token)
        return jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256", "ES256"],
            audience=settings.oauth_audience,
            issuer=settings.oauth_issuer_url,
            options={"require": ["exp", "sub"]},
        )
    except jwt.PyJWTError as exc:
        logger.warning("token verification failed: %s", exc)
        raise _unauthorized("토큰을 검증할 수 없습니다.") from exc


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> CurrentUser:
    if not settings.auth_required:
        return CurrentUser(id=settings.dev_user_id, claims={})

    if credentials is None or not credentials.credentials:
        raise _unauthorized("인증 토큰이 필요합니다.")

    claims = _decode_token(credentials.credentials, settings)
    subject = claims.get("sub")
    if not subject:
        raise _unauthorized("토큰에 sub 클레임이 없습니다.")

    return CurrentUser(id=str(subject), claims=claims)


CurrentUserDep = Annotated[CurrentUser, Depends(get_current_user)]
