"""User-scoped encrypted credentials for the Allinpay ZDX service."""

from __future__ import annotations

from dataclasses import dataclass

from octop.infra.connectors.crypto import decrypt_credentials, encrypt_credentials
from octop.infra.db.repos.secrets import SecretRepo

_SECRET_PREFIX = "zdx.credentials."


@dataclass(frozen=True)
class ZdxCredential:
    api_key: str
    userid: str


class ZdxCredentialStore:
    """Persist one encrypted ZDX credential pair per Octop user."""

    def __init__(self, secret_repo: SecretRepo) -> None:
        self._secret_repo = secret_repo

    @staticmethod
    def _key(user_id: int) -> str:
        return f"{_SECRET_PREFIX}{user_id}"

    def get(self, user_id: int) -> ZdxCredential | None:
        blob = self._secret_repo.get(self._key(user_id))
        if blob is None:
            return None
        data = decrypt_credentials(self._secret_repo, blob)
        api_key = data.get("api_key")
        userid = data.get("userid")
        if not isinstance(api_key, str) or not isinstance(userid, str):
            return None
        if not api_key.strip() or not userid.strip():
            return None
        return ZdxCredential(api_key=api_key, userid=userid)

    def save(self, user_id: int, *, api_key: str, userid: str) -> ZdxCredential:
        credential = self._validate(api_key=api_key, userid=userid)
        blob = encrypt_credentials(
            self._secret_repo,
            {"api_key": credential.api_key, "userid": credential.userid},
        )
        key = self._key(user_id)
        if self._secret_repo.get(key) is None:
            self._secret_repo.get_or_create(key, lambda: blob)
        else:
            self._secret_repo.rotate(key, blob)
        return credential

    def delete(self, user_id: int) -> None:
        self._secret_repo.delete(self._key(user_id))

    @staticmethod
    def _validate(*, api_key: str, userid: str) -> ZdxCredential:
        normalized_key = api_key.strip()
        normalized_userid = userid.strip()
        if not normalized_key or not normalized_userid:
            raise ValueError("ZDX api_key and userid are required")
        if any(ord(char) < 32 for char in (*normalized_key, *normalized_userid)):
            raise ValueError("ZDX api_key and userid must not contain control characters")
        return ZdxCredential(api_key=normalized_key, userid=normalized_userid)
