"""Direct, user-scoped client for the managed Tonglian ZDX model."""

from __future__ import annotations

import json
import re
from collections.abc import AsyncIterator
from typing import Any

import httpx

from octop.infra.agents.zdx_credentials import ZdxCredential


class ZdxDirectError(RuntimeError):
    """An upstream failure that must stay outside the normal Provider path."""

    def __init__(self, message: str, *, status_code: int = 0) -> None:
        super().__init__(message)
        self.status_code = status_code


_THINKING_OPEN_RE = re.compile(r"<(?:think|thinking)>", re.IGNORECASE)
_THINKING_CLOSE_RE = re.compile(r"</(?:think|thinking)>", re.IGNORECASE)
_THINKING_MARKERS = ("<think>", "<thinking>", "</think>", "</thinking>")


class _ThinkingFilter:
    """Remove inline thinking tags while preserving visible streaming text."""

    def __init__(self) -> None:
        self._pending = ""
        self._inside = False
        self._decided = False

    def feed(self, text: str) -> str:
        self._pending += text
        output: list[str] = []
        while self._pending:
            if not self._decided:
                open_match = _THINKING_OPEN_RE.search(self._pending)
                close_match = _THINKING_CLOSE_RE.search(self._pending)
                marker = self._first_marker(open_match, close_match)
                if marker is None:
                    break
                self._decided = True
                if marker[0] == "open":
                    output.append(self._pending[: marker[1].start()])
                    self._pending = self._pending[marker[1].end() :]
                    self._inside = True
                else:
                    # Some ZDX responses omit the opening tag and send the
                    # reasoning prefix followed only by a closing marker.
                    self._pending = self._pending[marker[1].end() :]
                continue

            if self._inside:
                close = _THINKING_CLOSE_RE.search(self._pending)
                if close is None:
                    self._pending = self._retain_close_marker_prefix(self._pending)
                    break
                self._pending = self._pending[close.end() :]
                self._inside = False
                continue

            open_match = _THINKING_OPEN_RE.search(self._pending)
            close_match = _THINKING_CLOSE_RE.search(self._pending)
            marker = self._first_marker(open_match, close_match)
            if marker is None:
                safe, self._pending = self._split_marker_safe_prefix(self._pending)
                output.append(safe)
                break

            if marker[0] == "open":
                output.append(self._pending[: marker[1].start()])
                self._pending = self._pending[marker[1].end() :]
                self._inside = True
            else:
                # Some ZDX responses omit the opening tag and send the
                # reasoning prefix followed only by a closing marker.
                self._pending = self._pending[marker[1].end() :]

        return "".join(output)

    def finish(self) -> str:
        if self._inside:
            self._pending = ""
            return ""
        pending = self._pending
        self._pending = ""
        return pending

    @staticmethod
    def _first_marker(
        open_match: re.Match[str] | None,
        close_match: re.Match[str] | None,
    ) -> tuple[str, re.Match[str]] | None:
        if open_match is None:
            return ("close", close_match) if close_match is not None else None
        if close_match is None or open_match.start() <= close_match.start():
            return ("open", open_match)
        return ("close", close_match)

    @classmethod
    def _split_marker_safe_prefix(cls, text: str) -> tuple[str, str]:
        max_marker_len = max(map(len, cls._markers()))
        lowered = text.lower()
        for index in range(max(0, len(text) - max_marker_len), len(text)):
            if any(marker.startswith(lowered[index:]) for marker in cls._markers()):
                keep = len(text) - index
                return text[:-keep], text[-keep:]
        return text, ""

    @classmethod
    def _retain_close_marker_prefix(cls, text: str) -> str:
        _, pending = cls._split_marker_safe_prefix(text)
        return pending or text[-max(map(len, cls._markers())) :]

    @staticmethod
    def _markers() -> tuple[str, ...]:
        return _THINKING_MARKERS


def _content_text(content: str | list[dict[str, Any]]) -> str:
    if isinstance(content, str):
        return content
    parts: list[str] = []
    for item in content:
        if not isinstance(item, dict):
            continue
        if item.get("type") == "text":
            text = item.get("text")
            if isinstance(text, str) and text:
                parts.append(text)
    return "\n\n".join(parts)


def build_zdx_payload(
    content: str | list[dict[str, Any]],
    *,
    userid: str,
    model: str = "auto",
    res_group_ids: str = "*",
    messages: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    """Build the restricted ZDX request body.

    ZDX orchestrates its own internal business tools. Octop must not forward
    its Harness tool catalog or tool-choice controls to this endpoint.
    """
    options: dict[str, Any] = {"forInner": True, "userid": userid}
    if res_group_ids:
        options["resGroupIds"] = res_group_ids
    return {
        "model": model.strip() or "auto",
        "stream": True,
        "messages": messages or [{"role": "user", "content": _content_text(content)}],
        "chatBizOptions": options,
    }


def _delta_from_payload(payload: Any) -> str:
    if not isinstance(payload, dict):
        return ""
    choices = payload.get("choices") or []
    if choices and isinstance(choices[0], dict):
        choice = choices[0]
        delta = choice.get("delta") or {}
        if isinstance(delta, dict):
            content = delta.get("content")
            if isinstance(content, str):
                return content
        message = choice.get("message") or {}
        if isinstance(message, dict):
            content = message.get("content")
            if isinstance(content, str):
                return content
    for key in ("content", "retmsg"):
        value = payload.get(key)
        if isinstance(value, str):
            return value
    return ""


def _error_detail(raw: str) -> str:
    try:
        payload = json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        return raw.strip()[:300]
    if isinstance(payload, dict):
        error = payload.get("error")
        if isinstance(error, dict):
            for key in ("message", "detail", "code"):
                value = error.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()[:300]
        for key in ("message", "detail", "retmsg"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()[:300]
    return ""


class TonglianZdxDirectClient:
    """Call ZDX without creating a Provider or caching user credentials."""

    def __init__(
        self,
        *,
        base_url: str,
        model: str = "auto",
        timeout_seconds: float = 120.0,
        res_group_ids: str = "*",
    ) -> None:
        base = base_url.rstrip("/")
        self._url = base + ("/chat/completions" if base.endswith("/v1") else "/v1/chat/completions")
        self._model = model.strip() or "auto"
        self._timeout = timeout_seconds
        self._res_group_ids = res_group_ids
        self._last_usage: dict[str, Any] | None = None

    @property
    def last_usage(self) -> dict[str, Any] | None:
        """Usage metadata returned by the upstream, when available."""
        return self._last_usage

    def _capture_usage(self, payload: Any) -> None:
        if not isinstance(payload, dict):
            return
        usage = payload.get("usage")
        if isinstance(usage, dict):
            self._last_usage = dict(usage)

    async def stream(
        self,
        content: str | list[dict[str, Any]],
        credential: ZdxCredential,
        *,
        messages: list[dict[str, str]] | None = None,
    ) -> AsyncIterator[str]:
        self._last_usage = None
        payload = build_zdx_payload(
            content,
            userid=credential.userid,
            model=self._model,
            res_group_ids=self._res_group_ids,
            messages=messages,
        )
        thinking_filter = _ThinkingFilter()
        headers = {
            "Authorization": f"Bearer {credential.api_key}",
            "Content-Type": "application/json; charset=UTF-8",
            "Accept": "text/event-stream",
            "Accept-Encoding": "identity",
        }
        timeout = httpx.Timeout(self._timeout)
        try:
            async with (
                httpx.AsyncClient(timeout=timeout) as client,
                client.stream("POST", self._url, json=payload, headers=headers) as response,
            ):
                if response.status_code >= 400:
                    detail = _error_detail((await response.aread()).decode("utf-8", "replace"))
                    suffix = f": {detail}" if detail else ""
                    raise ZdxDirectError(
                        f"ZDX request failed with HTTP {response.status_code}{suffix}",
                        status_code=response.status_code,
                    )
                content_type = response.headers.get("content-type", "")
                if "application/json" in content_type:
                    try:
                        payload_data = json.loads(await response.aread())
                        self._capture_usage(payload_data)
                        delta = _delta_from_payload(payload_data)
                    except json.JSONDecodeError:
                        delta = ""
                    if delta:
                        visible = thinking_filter.feed(delta)
                        if visible:
                            yield visible
                    visible = thinking_filter.finish()
                    if visible:
                        yield visible
                    return
                async for line in response.aiter_lines():
                    if not line.startswith("data:"):
                        continue
                    raw = line[5:].strip()
                    if not raw or raw == "[DONE]":
                        continue
                    try:
                        payload_data = json.loads(raw)
                        self._capture_usage(payload_data)
                        delta = _delta_from_payload(payload_data)
                    except json.JSONDecodeError:
                        continue
                    if delta:
                        visible = thinking_filter.feed(delta)
                        if visible:
                            yield visible
                visible = thinking_filter.finish()
                if visible:
                    yield visible
        except ZdxDirectError:
            raise
        except httpx.TimeoutException as exc:
            raise ZdxDirectError("ZDX request timed out", status_code=0) from exc
        except httpx.HTTPError as exc:
            raise ZdxDirectError("ZDX network request failed", status_code=0) from exc

    async def complete(
        self,
        content: str | list[dict[str, Any]],
        credential: ZdxCredential,
        *,
        messages: list[dict[str, str]] | None = None,
    ) -> str:
        """Collect a direct streamed response for one-shot utility calls."""
        chunks: list[str] = []
        async for delta in self.stream(content, credential, messages=messages):
            chunks.append(delta)
        return "".join(chunks).strip()
