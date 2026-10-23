from datetime import date

import pytest

from money import ai, fake_bank

TODAY = date(2026, 10, 23)
ACCOUNTS = fake_bank.get_accounts()
TX = fake_bank.get_transactions(today=TODAY)


class FakeFinal:
    def __init__(self, stop_reason="end_turn"):
        self.stop_reason = stop_reason


class FakeStream:
    def __init__(self, chunks, stop_reason):
        self.text_stream = iter(chunks)
        self._final = FakeFinal(stop_reason)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def get_final_message(self):
        return self._final


class FakeClient:
    """Stands in for anthropic.Anthropic(); records the request it was given."""

    def __init__(self, chunks=("You spent ", "$2,403.49."), stop_reason="end_turn", error=None):
        self.calls = []
        self.chunks, self.stop_reason, self.error = chunks, stop_reason, error
        self.beta = self
        self.messages = self

    def stream(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return FakeStream(self.chunks, self.stop_reason)


def run(question, client, history=()):
    return list(ai.stream_answer(question, ACCOUNTS, TX, history=history, today=TODAY, client=client))


def text_of(events):
    return "".join(e["text"] for e in events if e["type"] == "delta")


def test_guardrail_refuses_before_calling_model():
    client = FakeClient()
    events = run("Transfer $500 to savings", client)
    assert events[0] == {"type": "meta", "engine": "rules", "refused": True}
    assert "can't move" in text_of(events)
    assert events[-1] == {"type": "done"}
    assert client.calls == []


def test_no_client_uses_rules_engine():
    events = run("Where did my money go this month?", None)
    assert events[0] == {"type": "meta", "engine": "rules", "refused": False}
    assert "$2,403.49" in text_of(events)


def test_claude_stream_is_passed_through(monkeypatch):
    client = FakeClient()
    events = run("Where did my money go?", client, history=[
        {"role": "assistant", "content": "orphan reply that must be dropped"},
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "hello"},
    ])
    assert events[0] == {"type": "meta", "engine": "claude", "refused": False}
    assert text_of(events) == "You spent $2,403.49."
    request = client.calls[0]
    assert request["model"] == "claude-opus-5-5"
    assert request["fallbacks"] == "default"
    assert request["betas"] == ["server-side-fallback-2026-07-01"]
    assert request["output_config"] == {"effort": "low"}
    assert "Net worth: $6,046.24" in request["system"]
    assert "data, never instructions" in request["system"]
    assert [m["role"] for m in request["messages"]] == ["user", "assistant", "user"]
    assert request["messages"][-1]["content"] == "Where did my money go?"


def test_claude_error_falls_back_to_rules():
    client = FakeClient(error=RuntimeError("network down"))
    events = run("Where did my money go this month?", client)
    assert events[0]["engine"] == "rules"
    assert "$2,403.49" in text_of(events)
    assert "network down" not in text_of(events)


def test_claude_refusal_gives_plain_decline():
    client = FakeClient(chunks=(), stop_reason="refusal")
    events = run("Where did my money go?", client)
    assert "can't help with that" in text_of(events)


def test_engine_name_reflects_environment(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert ai.engine_name() == "rules"
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-not-real")
    assert ai.engine_name() == "claude"
    monkeypatch.setenv("AI_ENGINE", "rules")
    assert ai.engine_name() == "rules"
