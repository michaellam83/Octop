"""Tests for the user-scoped direct ZDX adapter."""

from __future__ import annotations

import json

import httpx
import pytest

from octop.infra.agents.zdx_direct import _ThinkingFilter, build_zdx_payload


def test_thinking_filter_hides_tagged_reasoning_across_chunks() -> None:
    thinking = _ThinkingFilter()

    visible = (
        "".join(
            thinking.feed(chunk)
            for chunk in ("<thinki", "ng>内部思考", "</think", "ing>最终", "答案")
        )
        + thinking.finish()
    )

    assert visible == "最终答案"


def test_thinking_filter_hides_orphan_closing_tag() -> None:
    thinking = _ThinkingFilter()

    visible = thinking.feed("内部思考") + thinking.feed("</thinking>") + thinking.feed("最终答案")
    visible += thinking.finish()

    assert visible == "最终答案"


def test_direct_zdx_payload_does_not_forward_octop_tools() -> None:
    payload = build_zdx_payload(
        "查询交易",
        userid="alice.pinyin",
        model="zdx-business-model",
        messages=[{"role": "user", "content": "查询交易"}],
    )

    assert payload["model"] == "zdx-business-model"
    assert payload["chatBizOptions"]["userid"] == "alice.pinyin"
    assert "tools" not in payload
    assert "tool_choice" not in payload


@pytest.mark.asyncio
async def test_direct_zdx_stream_captures_upstream_usage(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from octop.infra.agents.zdx_credentials import ZdxCredential
    from octop.infra.agents.zdx_direct import TonglianZdxDirectClient

    def handler(_request: httpx.Request) -> httpx.Response:
        body = b"".join(
            (
                b'data: {"choices":[{"delta":{"content":"answer"}}]}\n\n',
                b'data: {"usage":{"prompt_tokens":12,"completion_tokens":4,"total_tokens":16}}\n\n',
                b"data: [DONE]\n\n",
            )
        )
        return httpx.Response(
            200,
            headers={"content-type": "text/event-stream"},
            content=body,
        )

    real_client = httpx.AsyncClient

    def client_factory(*args: object, **kwargs: object) -> httpx.AsyncClient:
        client_kwargs = {**kwargs, "transport": httpx.MockTransport(handler)}
        return real_client(*args, **client_kwargs)

    monkeypatch.setattr("octop.infra.agents.zdx_direct.httpx.AsyncClient", client_factory)
    client = TonglianZdxDirectClient(base_url="https://example.com/v1")

    chunks = [
        delta
        async for delta in client.stream(
            "你好",
            ZdxCredential(userid="u", api_key="k"),
        )
    ]

    assert "".join(chunks) == "answer"
    assert client.last_usage == {
        "prompt_tokens": 12,
        "completion_tokens": 4,
        "total_tokens": 16,
    }


@pytest.mark.asyncio
async def test_direct_zdx_complete_collects_streamed_text(monkeypatch: pytest.MonkeyPatch) -> None:
    from octop.infra.agents.zdx_credentials import ZdxCredential
    from octop.infra.agents.zdx_direct import TonglianZdxDirectClient

    client = TonglianZdxDirectClient(base_url="https://example.com/v1")

    async def fake_stream(*_args: object, **_kwargs: object):
        yield "第一段"
        yield "第二段"

    monkeypatch.setattr(client, "stream", fake_stream)
    result = await client.complete(
        "draft",
        ZdxCredential(userid="u", api_key="k"),
        messages=[{"role": "user", "content": "draft"}],
    )

    assert result == "第一段第二段"


@pytest.mark.asyncio
async def test_direct_zdx_stream_filters_thinking_from_sse(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from octop.infra.agents.zdx_credentials import ZdxCredential
    from octop.infra.agents.zdx_direct import TonglianZdxDirectClient

    def handler(_request: httpx.Request) -> httpx.Response:
        lines = b"".join(
            (f'data: {{"choices":[{{"delta":{{"content":{json.dumps(chunk)}}}}}]}}\n\n').encode()
            for chunk in ("<thinki", "ng>内部思考", "</think", "ing>最终答案")
        )
        return httpx.Response(
            200,
            headers={"content-type": "text/event-stream"},
            content=lines + b"data: [DONE]\n\n",
        )

    real_client = httpx.AsyncClient

    def client_factory(*args: object, **kwargs: object) -> httpx.AsyncClient:
        client_kwargs = {**kwargs, "transport": httpx.MockTransport(handler)}
        return real_client(*args, **client_kwargs)

    monkeypatch.setattr("octop.infra.agents.zdx_direct.httpx.AsyncClient", client_factory)
    client = TonglianZdxDirectClient(base_url="https://example.com/v1")

    chunks = [
        delta
        async for delta in client.stream(
            "你好",
            ZdxCredential(userid="u", api_key="k"),
        )
    ]

    assert "".join(chunks) == "最终答案"
