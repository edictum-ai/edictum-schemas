# Workflow Adapter Conformance Fixtures

These fixtures prove behavioral conformance is the same across SDKs for the
adapter-level Workflow Gate behavior required by Spec 017 P6.

They extend the base workflow fixture model in
[`../workflow/README.md`](../workflow/README.md) with approval loop inputs,
non-tool stage-move operations, session lineage, evidence, reset-adjacent state
updates, blocked actions, and ordered audit-event expectations.

## File Class

Each suite file uses the `*.workflow-adapter.yaml` suffix.

## Top-Level Format

Each suite file contains:

- `suite`: stable suite identifier
- `version`: fixture format version
- `description`: short human summary
- `workflows`: named `kind: Workflow` documents used by the cases
- `fixtures`: ordered adapter conformance cases

## Fixture Case Format

Each fixture case contains:

- `id`: stable case identifier
- `workflow`: key from `workflows`
- `description`: short human summary
- `initial_state`: workflow state before any step runs
- `lineage`: optional event-lineage inputs such as `parent_session_id`
- `steps`: ordered intercepted calls and `set_stage_to` operations for the
  adapter under test

`initial_state` extends the workflow runtime state with the stable snapshot
fields needed for adapter audit assertions:

```yaml
session_id: session-001
active_stage: read-analyze
completed_stages: []
approvals: {}
evidence:
  reads: []
  stage_calls: {}
blocked_reason: null
pending_approval:
  required: false
```

Optional snapshot fields:

- `last_recorded_evidence`
- `last_blocked_action`

The current fixtures only assert stable fields on those records. Timestamp
fields are intentionally omitted from the YAML because they are runtime values.

## Step Format

Call steps reuse the base workflow fields and add adapter inputs:

```yaml
- id: push-after-approval
  call:
    tool: Bash
    args:
      command: git push origin feat/017-p6-workflow-conformance-fixtures
  approval_outcomes:
    - approved
  execution: success
  expect:
    decision: allow
    active_stage: commit-push
    completed_stages: [read-analyze, implement, local-verify, local-review]
    approvals:
      local-review: approved
    evidence:
      reads:
        - specs/017.md
      stage_calls:
        local-verify:
          - pytest
        commit-push:
          - git push origin feat/017-p6-workflow-conformance-fixtures
    blocked_reason: null
    pending_approval:
      required: false
    audit_events:
      - action: call_asked
        workflow:
          active_stage: local-review
          pending_approval:
            required: true
            stage_id: local-review
            message: Approve after reviewing the diff and pytest output
      - action: call_approval_granted
      - action: workflow_stage_advanced
      - action: call_allowed
      - action: call_executed
```

Field meanings:

- `call`: normalized tool name plus the tool arguments relevant to evaluation
- `approval_outcomes`: ordered approval responses the adapter should consume
- `execution`: post-decision execution outcome
- `expect`: expected decision, persisted workflow state, and audit events

Set-stage steps model non-destructive stage movement exposed as `setStage`,
`SetStage`, or `set_stage` by the SDKs:

```yaml
- id: set-stage-to-local-review
  set_stage_to: local-review
  expect:
    active_stage: local-review
    completed_stages: [read-analyze, implement, local-verify]
    approvals: {}
    evidence:
      reads: []
      stage_calls: {}
    blocked_reason: null
    pending_approval:
      required: true
      stage_id: local-review
      message: Approve after reviewing the diff and pytest output
    audit_events:
      - action: workflow_state_updated
        workflow:
          active_stage: local-review
          pending_approval:
            required: true
            stage_id: local-review
            message: Approve after reviewing the diff and pytest output
```

Field meanings:

- `set_stage_to`: named stage for non-destructive stage movement; these steps
  omit `call`, `approval_outcomes`, `execution`, and `expect.decision`

Supported `approval_outcomes` values in this fixture class:

- `approved`
- `rejected`

Supported `execution` values:

- `success`: the call executed successfully
- `error`: the call executed but failed
- `not_run`: the call never executed because it was blocked or paused

Supported `expect.decision` values:

- `allow`
- `block`
- `pause`

## Set-Stage Semantics

`set_stage_to` follows the shared set-stage model:

- the named stage becomes `active_stage`
- `completed_stages` becomes every stage before the target stage
- approvals and evidence are preserved
- `blocked_reason` and `last_blocked_action` are cleared
- `pending_approval` is recomputed immediately for the target stage
- the public event sequence is a single `workflow_state_updated`

## Audit Event Expectations

`expect.audit_events` is the ordered public event sequence for the step.

Each entry is a partial event assertion:

- `action` is always required
- unlisted event keys may be present
- listed nested `workflow` keys should match exactly

These fixtures use the canonical action names from the M1 terminology update:

- `call_allowed`
- `call_blocked`
- `call_asked`
- `call_approval_granted`
- `call_approval_blocked`
- `call_executed`
- `call_failed`
- `workflow_stage_advanced`
- `workflow_completed`
- `workflow_state_updated`

## Scope

These fixtures assert public adapter behavior only:

- workflow stage progression
- approval gating
- multi-round approval loops
- non-tool stage moves that emit `workflow_state_updated`
- blocked calls with workflow context
- session lineage on audit events
- workflow context on allowed, blocked, executed, and failed events
- post-execution recording that affects later stage evaluation
