#!/usr/bin/env python3
# Copyright Entropy Hackers. Licensed under the Apache License, Version 2.0.
"""Containerless "lightweight" agent runtime for an Artificial Moral
Societies run — a direct chat-completions API call per turn, full
context re-sent every time, no openclaw container/tools/persistent
memory. See STATUS.md's "light/memoryless vs. fully agentic"
comparison arm, deferred until this became relevant to Phase 1.

This isn't just a cheaper substitute for the openclaw path — it's
closer to how the literature this experiment is positioned against
actually runs its LLM agents: Han et al. 2025's own methodology
folds the round history into each round's prompt, one completion call
at a time (no external tool use); "NetworkGames" (arXiv:2511.21783)
explicitly builds each prompt from "game history from the last N
rounds" rather than a stateful agent. So this arm is the
methodologically-standard baseline, and the fully-agentic (tool-using,
per-container-memory) arm is the comparison's non-standard side.

Function-calling schema mirrors engine/plugins/society-tools/index.js
tool-for-tool (same names/params) — a lightweight and an openclaw agent
get the exact same actions, so the comparison is about runtime/memory
architecture, not tool availability. Currently covers the commons and
network_reciprocity tools (what the pilot needs); pd/governance tools
aren't mirrored here yet.

Context handling: each agent's full message history (system prompt +
every round's user/assistant/tool messages) is kept by the orchestrator
and persisted to a JSON file per agent after every turn — "memory"
here is explicit, inspectable state this script owns, not something
implicit inside a running container. No truncation/summarization
implemented: fine for the pilot's 15-20 rounds, a clear next step if a
longer run needs it.

Defaults to DeepSeek's hosted chat-completions API (OpenAI-compatible),
but talks to any OpenAI-compatible endpoint — pass a different
`base_url`/`model` (e.g. a local vLLM server, see
`tools/reports/local_model_setup.md`) to run this same harness against
a self-hosted model instead. `DEFAULT_MODEL` used to be DeepSeek's
"deepseek-chat", retired 2026-07-24 in favour of "deepseek-v4-flash" —
updated here to match, and to match what the openclaw agents in this
same experiment already use for their own DeepSeek calls, so the two
runtimes stay comparable on model version, not just architecture.
vLLM needs `--enable-auto-tool-choice` plus a `--tool-call-parser`
matching the served model family for the tool-calling loop below to
work at all — a plain vLLM server without those flags will just never
emit `tool_calls`.
"""

from __future__ import annotations

import http.client
import json
import os
import threading
import time
import urllib.error
import urllib.request
from collections import deque
from datetime import datetime, timezone
from pathlib import Path

DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEFAULT_MODEL = "deepseek-v4-flash"
MAX_TOOL_ITERS = 6  # guards against a runaway tool-call loop within one turn

# Per-call API usage log (JSONL, one line per model call) -- added
# 2026-08-12 after repeatedly not having token-level data to explain a
# cost surprise after the fact (see STATUS.md's GLM lesson). Path and
# a free-text run label are both environment-driven so callers (shell
# orchestration scripts, run_h2_full.py, etc.) don't need a code
# change to tag their own calls -- set AMS_RUN_LABEL before invoking.
CALL_LOG_PATH = os.environ.get(
    "AMS_CALL_LOG",
    str(Path(__file__).resolve().parent / "reports" / "raw_exports" / "api_call_log.jsonl"),
)
_call_log_lock = threading.Lock()


def log_call(model: str, base_url: str, ok: bool, usage: dict | None = None,
            error: str | None = None, run_label: str | None = None) -> None:
    """Appends one JSONL line per model call. `usage` is whatever the
    provider's response actually included (OpenAI-compatible APIs
    return {"prompt_tokens", "completion_tokens", "total_tokens"});
    left as null, not guessed, when a provider's envelope doesn't
    include it (e.g. MUG's custom gateway may not)."""
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "model": model,
        "base_url": base_url,
        "run_label": run_label or os.environ.get("AMS_RUN_LABEL", "unknown"),
        "ok": ok,
        "usage": usage,
        "error": error,
    }
    try:
        with _call_log_lock:
            Path(CALL_LOG_PATH).parent.mkdir(parents=True, exist_ok=True)
            with open(CALL_LOG_PATH, "a") as f:
                f.write(json.dumps(entry) + "\n")
    except OSError:
        pass  # logging must never break a run

# Retry-with-backoff for rate-limit errors, found necessary 2026-08-02:
# a 20-agent/15-round run against MedUniGraz's gateway with
# --max-parallel 10 failed 810/900 turns with "Rate limit exceeded"
# (per-client, requests/minute, per the platform's own docs) — isolated
# probing afterward showed no fixed burst threshold (concurrency=10
# batches succeeded in isolation), pointing at a cumulative
# rolling-window limit that only bites over a full run's sustained
# request rate, not a number cheap to determine exactly from outside.
# Retrying instead of guessing the exact safe --max-parallel.
MAX_RATE_LIMIT_RETRIES = 5
RATE_LIMIT_BASE_DELAY = 10.0  # seconds; doubles each retry


def _is_rate_limit_error(error_text: str) -> bool:
    t = error_text.lower()
    return "rate limit" in t or "429" in t


# MedUniGraz's actual requests/minute ceiling was never confirmed (the
# rate-limit-increase request drafted 2026-08-05 was never sent) — this
# is a conservative guess, not a documented number. --max-parallel
# alone doesn't bound requests/minute (fast responses let a small pool
# of workers still burst well above any per-minute ceiling), so this
# throttles actual call submission rate directly, shared across
# threads. DeepSeek isn't throttled this way — it has held up fine at
# --max-parallel 10 with retries alone.
MUG_AI_MAX_RPM = 30


class _RateLimiter:
    """Thread-safe sliding-window limiter: blocks `acquire()` until
    fewer than `max_per_minute` calls have started in the trailing 60s."""

    def __init__(self, max_per_minute: int):
        self.max_per_minute = max_per_minute
        self._timestamps: deque[float] = deque()
        self._lock = threading.Lock()

    def acquire(self) -> None:
        while True:
            with self._lock:
                now = time.monotonic()
                while self._timestamps and now - self._timestamps[0] >= 60.0:
                    self._timestamps.popleft()
                if len(self._timestamps) < self.max_per_minute:
                    self._timestamps.append(now)
                    return
                wait = 60.0 - (now - self._timestamps[0])
            time.sleep(max(wait, 0.05))


_mug_ai_limiter = _RateLimiter(MUG_AI_MAX_RPM)


def _object_schema(properties: dict, required: list[str] | None = None) -> dict:
    return {"type": "object", "properties": properties, "required": required or [], "additionalProperties": False}


SOCIETY_TOOLS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "society_get_state",
            "description": "Get the current experiment state: round, phase, which other agents you can see, your own and their reputation (if enabled), and last round's outcomes.",
            "parameters": _object_schema({}),
        },
    },
    {
        "type": "function",
        "function": {
            "name": "society_commons_contribute",
            "description": "Add to the shared commons pool.",
            "parameters": _object_schema(
                {
                    "amount": {"type": "number", "description": "Amount to contribute, must be positive."},
                    "reason": {"type": "string", "description": "A short, one-line reason for this action. Recorded for research analysis."},
                },
                ["amount"],
            ),
        },
    },
    {
        "type": "function",
        "function": {
            "name": "society_commons_extract",
            "description": "Take from the shared commons pool.",
            "parameters": _object_schema(
                {
                    "amount": {"type": "number", "description": "Amount to extract, must be positive and no more than the current pool."},
                    "reason": {"type": "string", "description": "A short, one-line reason for this action. Recorded for research analysis."},
                },
                ["amount"],
            ),
        },
    },
    {
        "type": "function",
        "function": {
            "name": "society_nr_choice",
            "description": "Make your single binary choice for this round of the network-reciprocity game (cooperate or defect) — applies simultaneously to every neighbour you're currently connected to. Only valid in the network_reciprocity scenario.",
            "parameters": _object_schema(
                {
                    "choice": {"type": "string", "enum": ["cooperate", "defect"], "description": "Your choice this round."},
                    "reason": {"type": "string", "description": "A short, one-line reason for this choice. Recorded for research analysis."},
                },
                ["choice"],
            ),
        },
    },
    {
        "type": "function",
        "function": {
            "name": "society_triage_send",
            "description": "Refer/send part of your resource to a specific colleague you can see, trusting them to use it well — this is an act of vulnerability, not a guaranteed exchange: the amount is boosted on arrival, but only reaches that one colleague, and there's no guarantee they reciprocate. Only valid in the triage scenario.",
            "parameters": _object_schema(
                {
                    "target_agent_id": {"type": "string", "description": "Which visible colleague to send to."},
                    "amount": {"type": "number", "description": "Amount to send, must be positive."},
                    "reason": {"type": "string", "description": "A short, one-line reason for this action. Recorded for research analysis."},
                },
                ["target_agent_id", "amount"],
            ),
        },
    },
    {
        "type": "function",
        "function": {
            "name": "society_triage_keep",
            "description": "Keep this resource for your own patient instead of sending it to a colleague. Only valid in the triage scenario.",
            "parameters": _object_schema(
                {
                    "amount": {"type": "number", "description": "Amount to keep, must be positive."},
                    "reason": {"type": "string", "description": "A short, one-line reason for this action. Recorded for research analysis."},
                },
                ["amount"],
            ),
        },
    },
    {
        "type": "function",
        "function": {
            "name": "society_report",
            "description": "Report another agent's behaviour to the group ledger. Does not itself apply any penalty — see society_sanction for that.",
            "parameters": _object_schema(
                {"target_agent_id": {"type": "string"}, "reason": {"type": "string"}},
                ["target_agent_id", "reason"],
            ),
        },
    },
    {
        "type": "function",
        "function": {
            "name": "society_sanction",
            "description": "Sanction another agent, if sanctioning is enabled in this experiment condition. Reduces their reputation.",
            "parameters": _object_schema(
                {"target_agent_id": {"type": "string"}, "type": {"type": "string"}, "reason": {"type": "string"}},
                ["target_agent_id", "type", "reason"],
            ),
        },
    },
]

# tool name -> (http method, service path). GET tools (society_get_state)
# take no body.
# The one action that actually resolves an agent's round (as opposed
# to informational/optional calls like society_get_state, or
# supplementary ones like society_report/society_sanction that may
# legitimately precede or follow the main action). Auto-ending the
# turn right after one of these succeeds sidesteps a real,
# reproducible failure mode seen across multiple models (Mistral-Large-3
# via the JSON-mode gateway path, a locally-hosted Qwen3-32B via the
# native path): after taking the correct action, the model doesn't
# reliably emit its own stop signal and instead loops
# (repeated get_state calls, or even repeated duplicate actions) until
# MAX_TOOL_ITERS kills the turn. Rather than rely on every model to
# self-terminate correctly, enforce the one-action-per-round rule in
# code. Found and fixed 2026-08-07.
PRIMARY_ACTION_TOOLS = {
    "society_commons_contribute", "society_commons_extract",
    "society_nr_choice", "society_triage_send", "society_triage_keep",
}

TOOL_ENDPOINTS: dict[str, tuple[str, str]] = {
    "society_get_state": ("GET", "/state"),
    "society_commons_contribute": ("POST", "/commons/contribute"),
    "society_commons_extract": ("POST", "/commons/extract"),
    "society_nr_choice": ("POST", "/nr/choice"),
    "society_triage_send": ("POST", "/triage/send"),
    "society_triage_keep": ("POST", "/triage/keep"),
    "society_report": ("POST", "/report"),
    "society_sanction": ("POST", "/sanction"),
}


def service_call(service_url: str, token: str, method: str, path: str, body: dict | None = None) -> dict:
    req = urllib.request.Request(
        f"{service_url.rstrip('/')}{path}",
        method=method,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        data=json.dumps(body).encode() if body is not None else None,
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return {"error": e.read().decode(errors="replace"), "status": e.code}


def call_model(messages: list[dict], api_key: str, model: str = DEFAULT_MODEL, base_url: str = DEEPSEEK_BASE_URL) -> dict:
    req = urllib.request.Request(
        f"{base_url.rstrip('/')}/chat/completions",
        method="POST",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        data=json.dumps({"model": model, "messages": messages, "tools": SOCIETY_TOOLS, "tool_choice": "auto"}).encode(),
    )
    delay = RATE_LIMIT_BASE_DELAY
    for attempt in range(MAX_RATE_LIMIT_RETRIES + 1):
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read())
                log_call(model, base_url, ok=True, usage=data.get("usage"))
                return data
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors="replace")
            if attempt < MAX_RATE_LIMIT_RETRIES and _is_rate_limit_error(body):
                time.sleep(delay)
                delay *= 2
                continue
            log_call(model, base_url, ok=False, error=body[:300])
            return {"error": body}
        except (urllib.error.URLError, ConnectionError, TimeoutError, http.client.HTTPException) as e:
            # Transient network failures (dropped connections, read
            # timeouts) — not rate-limit-specific, but just as retryable.
            # Found the hard way, 2026-08-06: an uncaught RemoteDisconnected
            # here crashed a whole 15-round batch mid-run (same for a
            # TimeoutError on a different backend the same day) — these
            # used to propagate straight up and kill the entire script
            # instead of just failing one turn.
            if attempt < MAX_RATE_LIMIT_RETRIES:
                time.sleep(delay)
                delay *= 2
                continue
            log_call(model, base_url, ok=False, error=f"network error after {MAX_RATE_LIMIT_RETRIES} retries: {e}")
            return {"error": f"network error after {MAX_RATE_LIMIT_RETRIES} retries: {e}"}


def _tools_as_text() -> str:
    """Renders SOCIETY_TOOLS as a plain-text tool catalog, for backends
    with no native function-calling support (see call_model_json_mode's
    docstring). Generated from the same SOCIETY_TOOLS list call_model
    uses, so the two paths can't drift out of sync with each other."""
    lines = []
    for t in SOCIETY_TOOLS:
        fn = t["function"]
        props = fn["parameters"].get("properties", {})
        required = set(fn["parameters"].get("required", []))
        args_desc = ", ".join(
            f"{name}{'*' if name in required else ''}: {spec.get('type', 'any')}" + (f" ({spec['description']})" if spec.get("description") else "")
            for name, spec in props.items()
        ) or "no arguments"
        lines.append(f"- {fn['name']}: {fn['description']}\n  arguments: {args_desc}  (* = required)")
    return "\n".join(lines)


JSON_MODE_TOOL_INSTRUCTIONS = (
    "\n\nYou have access to the following tools, but this chat interface has no native "
    "function-calling support — you must call a tool by replying with ONLY a single JSON "
    "object, nothing else before or after it:\n"
    '{"tool": "<tool_name>", "arguments": {...}}\n\n'
    "When you are done acting for this turn (no more tool calls needed this round), reply "
    "with ONLY:\n"
    '{"tool": null}\n\n'
    "Tools:\n" + _tools_as_text()
)


def _extract_json_object(text: str) -> dict | None:
    """Best-effort JSON object extraction from a model's raw text reply
    — strips markdown code fences and surrounding prose, since a model
    without native structured output sometimes doesn't follow the
    'ONLY a JSON object' instruction exactly."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        return None
    try:
        return json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None


def call_model_json_mode(messages: list[dict], client_id: str, client_secret: str, model: str, base_url: str) -> dict:
    """For backends with a custom (non-OpenAI-compatible) envelope and
    no native tool-calling — currently written against MedUniGraz's
    internal AI gateway (X-Client-ID/X-Client-Secret headers,
    response.data.content), confirmed via its API docs (v1.0.7) that
    `tools`/`tool_choice`/`functions` aren't supported request fields
    at all, matching the 400 "Extra inputs are not permitted" this
    returns if you try. Returns {"content": str} on success or
    {"error": str} on failure, deliberately not the raw provider
    envelope, so run_agent_turn_json_mode doesn't need to know which
    custom backend it's talking to."""
    # `temperature` deliberately omitted, not hardcoded: reasoning-mode
    # models on this gateway (e.g. claude-opus-4-6) reject it outright
    # unless `reasoningEffort: "none"` is also set ("Field 'temperature'
    # ... is only supported when reasoningEffort is 'none'") — rather
    # than special-case every model's quirks here, let the gateway use
    # each model's own default.
    req = urllib.request.Request(
        f"{base_url.rstrip('/')}/api/v1/llm/chat",
        method="POST",
        headers={"X-Client-ID": client_id, "X-Client-Secret": client_secret, "Content-Type": "application/json"},
        data=json.dumps({"model": model, "messages": messages, "maxTokens": 1000}).encode(),
    )
    delay = RATE_LIMIT_BASE_DELAY
    for attempt in range(MAX_RATE_LIMIT_RETRIES + 1):
        _mug_ai_limiter.acquire()
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                body = json.loads(resp.read())
                # Not confirmed whether MUG's envelope includes usage at
                # all (no documented schema) -- captured defensively
                # under either common key, left null rather than
                # guessed if neither is present.
                usage = body.get("data", {}).get("usage") or body.get("usage")
                log_call(model, base_url, ok=True, usage=usage)
                return {"content": body["data"]["content"]}
        except urllib.error.HTTPError as e:
            err_body = e.read().decode(errors="replace")
            if attempt < MAX_RATE_LIMIT_RETRIES and _is_rate_limit_error(err_body):
                time.sleep(delay)
                delay *= 2
                continue
            log_call(model, base_url, ok=False, error=err_body[:300])
            return {"error": err_body}
        except (urllib.error.URLError, ConnectionError, TimeoutError, http.client.HTTPException) as e:
            # Same transient-network-failure handling as call_model() —
            # see its comment for why this was added 2026-08-06.
            if attempt < MAX_RATE_LIMIT_RETRIES:
                time.sleep(delay)
                delay *= 2
                continue
            log_call(model, base_url, ok=False, error=f"network error after {MAX_RATE_LIMIT_RETRIES} retries: {e}")
            return {"error": f"network error after {MAX_RATE_LIMIT_RETRIES} retries: {e}"}


def run_agent_turn_json_mode(
    agent_id: str,
    api_token: str,
    service_url: str,
    context_path: Path,
    system_prompt: str,
    round_message: str,
    client_id: str,
    client_secret: str,
    model: str,
    base_url: str,
) -> "TurnResult":
    """Same job as run_agent_turn, for a backend without native tool-
    calling (see call_model_json_mode) — the model expresses tool calls
    as JSON text instead of a structured tool_calls field, which we
    parse ourselves. The persisted context stays plain
    system/user/assistant messages (no `tool` role, no `tool_call_id`
    — this API doesn't have a concept of either), so context files from
    this path and from run_agent_turn's are NOT interchangeable; keep
    them in separate context directories per model/backend. Also note:
    this backend's `messages` schema only accepts 'user'/'assistant'
    roles (confirmed by a live 'role: Input should be user or
    assistant' validation error) — no 'system' role at all, unlike
    every other backend this codebase talks to. The system prompt is
    folded into the first user message instead."""
    if context_path.exists():
        messages = json.loads(context_path.read_text())
        messages.append({"role": "user", "content": round_message})
    else:
        # merged into one message, not two consecutive 'user' turns —
        # untested whether this backend requires strict alternation,
        # safer not to find out the hard way.
        messages = [{"role": "user", "content": system_prompt + JSON_MODE_TOOL_INSTRUCTIONS + "\n\n" + round_message}]

    tool_calls_made: list[str] = []
    try:
        for _ in range(MAX_TOOL_ITERS):
            response = call_model_json_mode(messages, client_id, client_secret, model, base_url)
            if "error" in response:
                return TurnResult(False, str(response["error"])[:300])
            content = response["content"]
            messages.append({"role": "assistant", "content": content})
            parsed = _extract_json_object(content)
            if parsed is None or not parsed.get("tool"):
                break
            name = parsed["tool"]
            args = parsed.get("arguments", {}) or {}
            if name not in TOOL_ENDPOINTS:
                result = {"error": f"unknown tool {name}"}
            else:
                method, path = TOOL_ENDPOINTS[name]
                result = service_call(service_url, api_token, method, path, args if method == "POST" else None)
            tool_calls_made.append(name)
            if name in PRIMARY_ACTION_TOOLS and "error" not in result:
                break
            messages.append({"role": "user", "content": f"Tool result for {name}: {json.dumps(result)}\n\nContinue with your turn, or reply {{\"tool\": null}} if you're done."})
        else:
            return TurnResult(False, f"hit MAX_TOOL_ITERS={MAX_TOOL_ITERS} without a final reply (tool calls so far: {tool_calls_made})")
    finally:
        save_context(context_path, messages)

    return TurnResult(True, f"tool calls: {tool_calls_made}")


def load_context(context_path: Path, system_prompt: str) -> list[dict]:
    if context_path.exists():
        return json.loads(context_path.read_text())
    return [{"role": "system", "content": system_prompt}]


def save_context(context_path: Path, messages: list[dict]) -> None:
    context_path.parent.mkdir(parents=True, exist_ok=True)
    context_path.write_text(json.dumps(messages, indent=2))


class TurnResult:
    def __init__(self, ok: bool, detail: str):
        self.ok = ok
        self.detail = detail


def run_agent_turn(
    agent_id: str,
    api_token: str,
    service_url: str,
    context_path: Path,
    system_prompt: str,
    round_message: str,
    api_key: str,
    model: str = DEFAULT_MODEL,
    base_url: str = DEEPSEEK_BASE_URL,
) -> TurnResult:
    """One round for one lightweight agent: append the round prompt to
    its persisted context, run the model/tool-call loop until it stops
    calling tools (or hits MAX_TOOL_ITERS), persist the full context
    back, return a short summary. Context is saved in a `finally` so a
    mid-turn failure doesn't lose the round's partial transcript."""
    messages = load_context(context_path, system_prompt)
    messages.append({"role": "user", "content": round_message})

    tool_calls_made: list[str] = []
    try:
        for _ in range(MAX_TOOL_ITERS):
            response = call_model(messages, api_key, model, base_url)
            if "error" in response:
                return TurnResult(False, str(response["error"])[:300])
            choice = response["choices"][0]["message"]
            messages.append(choice)
            tool_calls = choice.get("tool_calls") or []
            if not tool_calls:
                break
            primary_action_done = False
            for call in tool_calls:
                name = call["function"]["name"]
                try:
                    args = json.loads(call["function"]["arguments"] or "{}")
                except json.JSONDecodeError:
                    args = {}
                if name not in TOOL_ENDPOINTS:
                    result = {"error": f"unknown tool {name}"}
                else:
                    method, path = TOOL_ENDPOINTS[name]
                    result = service_call(service_url, api_token, method, path, args if method == "POST" else None)
                tool_calls_made.append(name)
                messages.append({"role": "tool", "tool_call_id": call["id"], "content": json.dumps(result)})
                if name in PRIMARY_ACTION_TOOLS and "error" not in result:
                    primary_action_done = True
            if primary_action_done:
                break
        else:
            return TurnResult(False, f"hit MAX_TOOL_ITERS={MAX_TOOL_ITERS} without a final reply (tool calls so far: {tool_calls_made})")
    finally:
        save_context(context_path, messages)

    return TurnResult(True, f"tool calls: {tool_calls_made}")
