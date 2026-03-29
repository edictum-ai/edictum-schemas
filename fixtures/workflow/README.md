# Workflow Conformance Fixtures

These fixtures define shared, runtime-agnostic behavior for Spec 008 Workflow Gates.

They are intended to be consumed by the Go, Python, and TypeScript SDKs so each
runtime can prove the same stage, approval, and evidence semantics.

## Format

Each fixture file is a YAML suite with these top-level fields:

- `suite`: stable suite identifier
- `version`: fixture format version
- `description`: short human summary
- `workflows`: named `kind: Workflow` documents used by the fixtures in the file
- `fixtures`: ordered conformance cases

Each fixture case contains:

- `id`: stable case identifier
- `workflow`: key from `workflows`
- `description`: short human summary
- `initial_state`: workflow instance state before any steps run
- `steps`: ordered intercepted tool calls and their expected outcome

## State Model

`initial_state` and `expect` use the same shape:

```yaml
session_id: session-001
active_stage: read-context
completed_stages: []
approvals: {}
evidence:
  reads: []
  stage_calls: {}
```

Field meanings:

- `session_id`: workflow instance key input
- `active_stage`: currently active stage id
- `completed_stages`: completed stage ids in completion order
- `approvals`: mapping of stage id to approval outcome
- `evidence.reads`: successfully recorded file reads for the workflow instance
- `evidence.stage_calls`: successful stage-scoped command evidence

## Step Model

Each step describes one intercepted call:

```yaml
- id: attempt-edit
  call:
    tool: Edit
    args:
      path: src/app.ts
  execution: not_run
  expect:
    decision: deny
    active_stage: read-context
    completed_stages: []
    approvals: {}
    evidence:
      reads: []
      stage_calls: {}
```

Field meanings:

- `call`: normalized tool name plus tool arguments relevant to evaluation
- `execution`: post-decision execution outcome
- `expect`: expected workflow decision and final persisted state after the step

Supported `execution` values:

- `success`: the call executed successfully, so post-success evidence must be recorded
- `error`: the call was allowed to execute but failed, so no new evidence may be recorded
- `not_run`: the call was denied or paused before execution

Supported `expect.decision` values:

- `allow`: the current call is accepted for execution
- `deny`: the current call is blocked
- `pause`: the current call is paused pending approval

Optional expectation fields:

- `message_contains`: stable substring for the blocking or pause reason
- `approval_requested_for`: stage id that triggered an approval pause

## Scope

These fixtures are intentionally minimal:

- they assert workflow semantics, not audit payload shape
- they assert normalized tool calls, not SDK-specific request envelopes
- they assert persisted state after each step, not internal evaluator structure
