# Workflow Coding-Guard Fixtures

These fixtures define workflow-specific behavior for the Spec 017 P7
`coding-guard` workflow.

They reuse the shared workflow fixture model in
[`../workflow/README.md`](../workflow/README.md) and add the minimum inputs
needed to cover approval and operator reset behavior for this named workflow.

## File Class

Each suite file uses the `*.workflow-coding-guard.yaml` suffix.

## Top-Level Format

Each suite file contains:

- `suite`: stable suite identifier
- `version`: fixture format version
- `description`: short human summary
- `workflows`: named `kind: Workflow` documents used by the cases
- `fixtures`: ordered coding-guard conformance cases

## Fixture Case Format

Each fixture case contains:

- `id`: stable case identifier
- `workflow`: key from `workflows`
- `description`: short human summary
- `initial_state`: workflow state before any step runs
- `steps`: ordered intercepted calls and reset operations

## Step Format

Call steps reuse the base workflow fixture fields and may add approval loop
inputs:

```yaml
- id: approve-review-and-edit-docs
  call:
    tool: Edit
    args:
      path: README.md
  approval_outcomes:
    - approved
  execution: success
  expect:
    decision: allow
    active_stage: docs-update
    completed_stages:
      - read-analyze
      - create-branch
      - baseline-verify
      - implement
      - local-verify
      - external-review
```

Reset steps model the operator reset path from Spec 008:

```yaml
- id: reset-to-implement
  reset_to: implement
  expect:
    active_stage: implement
    completed_stages:
      - read-analyze
      - create-branch
      - baseline-verify
```

Field meanings:

- `approval_outcomes`: ordered approval responses the runtime should consume
- `reset_to`: named stage for the operator reset; reset steps omit `call` and
  `execution`

Supported `approval_outcomes` values in this fixture class:

- `approved`
- `rejected`

## Reset Semantics

`reset_to` follows the Spec 008 reset model:

- the named stage becomes `active_stage`
- later stages are removed from `completed_stages`
- approvals for the reset stage and later stages are cleared
- later-stage `stage_calls` evidence is cleared so later gates must be rerun

## Scope

These fixtures assert the public behavior of the `coding-guard` workflow only:

- 10-stage progression through the coding process
- blocked git commands in the wrong stage
- approval gating at `external-review`
- operator reset back to `implement` after review or CI findings
