# Trace Update: monocle-apptrace `0.8.14` → `0.8.7b1`

This document captures the full set of differences observed after switching the
`monocle-apptrace` dependency from the PyPI release **`0.8.14`** to the local
wheel **`0.8.7b1`** (`monocle_apptrace-0.8.7b1-py3-none-any.whl`).

## Traces Compared

| Role | Trace ID | File | Version |
|------|----------|------|---------|
| Old (baseline) | `08171c22f84f8d7317adc609d426e913` | `monocle_trace_okahu_demos_ms_openai_sequential_travel_08171c22f84f8d7317adc609d426e913_2026-09-01_21.16.07.json` | `0.8.14` |
| New (current) | `68ee1f66804b4e935071ffbaecc21719` | `monocle_trace_okahu_demos_ms_openai_sequential_travel_68ee1f66804b4e935071ffbaecc21719_2026-09-01_23.22.09.json` | `0.8.7b1` |

Both traces run the identical **sequential travel** workflow with the same
prompt and the same four agents:

```
DestinationResearcher → FlightPlanner → HotelPlanner → ItineraryWriter
```

## Dependency Change

`pyproject.toml`:

```toml
dependencies = [
    ...
    "monocle-apptrace",
]

[tool.uv.sources]
monocle-apptrace = { path = "monocle_apptrace-0.8.7b1-py3-none-any.whl" }
```

`uv sync` result:

```
- monocle-apptrace==0.8.14
+ monocle-apptrace==0.8.7b1 (from file:///.../monocle_apptrace-0.8.7b1-py3-none-any.whl)
```

---

## Summary of Differences

| # | Area | Old `0.8.14` | New `0.8.7b1` |
|---|------|--------------|---------------|
| 1 | Version tag | `monocle_apptrace.version: 0.8.14` | `monocle_apptrace.version: 0.8.7b1` |
| 2 | LLM response capture | `data.output` empty (`{}`) | `data.output.response` contains full LLM output |
| 3 | Inference span subtype | no `span.subtype` | `span.subtype`: `turn_end` / `tool_call` |
| 4 | Tool entity on inference | `entity.count: 2` (no tool) | `entity.count: 3`, `entity.3 = tool.function` |
| 5 | Tool → decision linkage | none | `inference.decision.span.id` on tool + agent spans |
| 6 | Last-inference pointer | none | `last.inference` on invocation + turn spans |
| 7 | Finish metadata | tokens only | adds `finish_reason` + `finish_type` |

Everything else — trace/span hierarchy, span names, agent order, scoping
(`scope.agentic.turn` / `scope.agentic.invocation`), tool `data.input` /
`data.output`, and the top-level `workflow` + `Workflow.run` spans — is
unchanged.

---

## Detailed Changes

### 1. Version Tag

Every span's `attributes.monocle_apptrace.version` changed from `0.8.14` to
`0.8.7b1`.

### 2. LLM Response Capture (most significant)

In `0.8.14`, inference spans
(`openai.resources.responses.responses.AsyncResponses.create`) recorded an
**empty** `data.output`:

```jsonc
// OLD 0.8.14
{
    "name": "data.output",
    "attributes": {}
}
```

In `0.8.7b1`, the actual model output is captured:

```jsonc
// NEW 0.8.7b1
{
    "name": "data.output",
    "attributes": {
        "response": "{\"assistant\": \"**Best Season to Visit San Francisco:** ...\"}"
    }
}
```

This applies to plain completions (`assistant` text) and tool-calling turns
(`tools` array with `tool_id` / `tool_name` / `tool_arguments`).

### 3. Inference Span Subtype

`0.8.7b1` classifies each inference span with a `span.subtype`:

- `turn_end` — the inference that produces the final assistant message for a turn.
- `tool_call` — the inference that decides to invoke one or more tools.

`0.8.14` inference spans carry **no** `span.subtype`.

### 4. Tool Entity on Inference Spans

When an inference decides to call a tool, `0.8.7b1` records the tool as an
additional entity on the inference span:

```jsonc
// NEW 0.8.7b1 (tool_call inference)
"entity.3.name": "search_flights",
"entity.3.type": "tool.function",
"entity.count": 3,
"span.subtype": "tool_call"
```

`0.8.14` inference spans stay at `entity.count: 2` (inference provider + model
only) and never describe the tool at the inference level.

### 5. Tool → Inference Decision Linkage

`0.8.7b1` connects executed tool calls and downstream agent invocations back to
the inference span that decided them via `inference.decision.span.id`:

```jsonc
// NEW 0.8.7b1 — FunctionTool.invoke
"span.type": "agentic.tool.invocation",
"span.subtype": "content_generation",
"inference.decision.span.id": "8630ebbd01b663d7"
```

```jsonc
// NEW 0.8.7b1 — AgentExecutor.execute
"span.type": "agentic.invocation",
"inference.decision.span.id": "c1adb236306f9b0f"
```

`0.8.14` tool `invoke` spans have `span.subtype: content_generation` but **no**
`inference.decision.span.id`, and agent-executor spans have no decision link.

> Note: not every tool-invoke span carries the decision id in the new trace —
> when multiple tools fire from one decision, at least one span links back while
> the sibling may omit it.

### 6. Last-Inference Pointer

`0.8.7b1` adds a `last.inference` attribute (formatted `<span_id>:*`) to:

- `agentic.invocation` spans (`AgentExecutor.execute`)
- the `agentic.turn` span (`Workflow.run`)

```jsonc
// NEW 0.8.7b1
"last.inference": "af7e1a2677efe104:*"
```

`0.8.14` does not emit `last.inference`.

### 7. Finish Metadata

The `metadata` event on inference spans is enriched in `0.8.7b1`:

```jsonc
// OLD 0.8.14
"attributes": {
    "completion_tokens": 180,
    "prompt_tokens": 89,
    "total_tokens": 269,
    "cache_read_input_tokens": 0
}
```

```jsonc
// NEW 0.8.7b1
"attributes": {
    "completion_tokens": 174,
    "prompt_tokens": 89,
    "total_tokens": 263,
    "cache_read_input_tokens": 0,
    "finish_reason": "stop",       // or "tool_calls"
    "finish_type": "success"       // or "tool_call"
}
```

Observed pairings:

| `finish_reason` | `finish_type` |
|-----------------|---------------|
| `stop` | `success` |
| `tool_calls` | `tool_call` |

---

## What Stayed the Same

- Span names and OpenTelemetry hierarchy (parent/child relationships).
- Agent sequence and the four executors.
- `workflow` (root) and `Workflow.run` (`agentic.turn`) spans, including
  `monocle.last.agent.invocation.id` / `monocle.last.agent.name`.
- Scoping via `scope.agentic.turn` and `scope.agentic.invocation`.
- Tool-level `data.input` and `data.output` (tool results were already captured
  in both versions).
- `service.name`, `resource`, and `span_source` semantics.

---

## Impact

Switching to the local `0.8.7b1` wheel yields **richer instrumentation** for
this workflow:

- Captured LLM responses (previously blank in `0.8.14`).
- Explicit inference/tool decision linkage (`inference.decision.span.id`,
  `last.inference`).
- Inference span subtypes (`turn_end`, `tool_call`).
- Finish-reason / finish-type metadata.

These additions improve traceability and evaluation quality (e.g. Okahu can now
inspect model outputs and reconstruct which inference drove each tool call),
at the cost of larger trace payloads because response bodies are now stored.
