---
name: te-tester-gen-spec
description: Generate or refine a QA-focused feature specification from a ticket, requirement note, existing spec, UI, or code pointers.
allowed-tools: AskUserQuestion, Bash, Read, Write, Edit, Glob, Grep
---

# /te-tester-gen-spec

You are helping a tester/QA analyst create a clear, testable feature specification. The output must be detailed enough for QA to generate test cases and for dev/BA to review the expected behavior.

This command is QA-focused. It does not replace the BA source-of-truth process. If this repository already has official feature specs, read them first and keep the generated QA spec consistent with them.

## Operating Principles

- Prefer existing source-of-truth documents over guessing.
- Write observable behavior, not implementation assumptions.
- Separate confirmed facts from assumptions.
- Every requirement must be testable.
- Cover normal flow, abnormal flow, edge cases, permissions, data states, integrations, and notifications.
- Do not silently rewrite official source-of-truth files unless the user explicitly asks to save changes.
- If information is missing, ask concise questions. If the user wants you to continue, mark the item as an assumption.

## Step 1 - Understand The Request

Use `$ARGUMENTS` as the initial clue. It may be:

- a Jira key or Jira link;
- a feature ID;
- a local file path;
- a feature name;
- a short requirement description.

If the request is unclear, ask the user for:

1. Feature/module name.
2. Source input: Jira, existing spec, design, code path, or free-text requirement.
3. Desired output location: chat only or save to file.

Do not ask more than necessary before reading available context.

## Step 2 - Collect Context

Read all relevant local documents that exist:

- `CLAUDE.md`
- `README.md`
- `constitution.md`
- `SPECS_INDEX.md`
- matching `spec.md`
- matching `acceptance.md`
- matching `tech.md`
- matching `meta.yml`
- related rule files: `.claude/rules/**` của repo hiện tại, if present
- user-provided files or paths

If this is an `optis-specs` repository, find the feature by checking:

- `app-swatch/features/<FEATURE_ID>/`
- `app-option/features/<FEATURE_ID>/`

If the user provides a code path, read nearby files only as needed to infer behavior. Clearly label any inference from code.

## Step 3 - Identify The Feature Boundary

Before drafting, identify:

- Product/app.
- Feature/module name.
- Business goal.
- Actor/user roles.
- Entry points/screens/API routes.
- In-scope behavior.
- Out-of-scope behavior.
- Dependencies on other modules.
- External systems involved.

If the feature may already exist, do not create a duplicate concept. Reuse the existing feature identity and note that this is a QA spec for that feature.

## Step 4 - Extract Requirements

Extract and structure these areas:

- Functional requirements.
- Business rules.
- Validation rules.
- Data rules and default values.
- Permissions and plan gates.
- UI states.
- Loading states.
- Empty states.
- Error states.
- Success/failure notifications.
- Integration behavior.
- Audit/log/tracking behavior, if visible to QA or important for verification.
- Lifecycle behavior: install, first use, normal use, update, retry, uninstall/reinstall, data retention.

For each requirement, make it concrete:

- Use exact limits, statuses, field names, button names, messages, URLs, or labels when known.
- Use examples for formulas, ranges, mapping rules, and fallback behavior.
- Avoid vague phrases such as "works properly", "handles errors", or "user-friendly".

## Step 5 - Resolve Gaps

Make a short "Questions / Assumptions" list while drafting.

Ask the user only for requirement-level decisions that block a useful spec, such as:

- unclear expected result;
- conflicting sources;
- missing validation limits;
- unclear permission or plan behavior;
- unclear error handling;
- unclear scope boundary.

If the user does not provide an answer and wants a draft anyway, write the unresolved item as:

`Assumption: <specific assumption>. Needs confirmation from BA/PO.`

## Step 6 - Generate QA Spec

Output in this structure:

```md
# QA Spec - <Feature Name>

## 1. Overview
- Product/App:
- Feature:
- Purpose:
- Primary users:
- Source materials:
- Status:

## 2. Scope
### In Scope
- ...

### Out Of Scope
- ...

## 3. Preconditions
- Environment:
- User/account:
- Store/data:
- Permissions/plan:
- External services:

## 4. Functional Requirements
| ID | Requirement | Priority | Notes |
| --- | --- | --- | --- |
| REQ-001 | ... | Must | ... |

## 5. Business Rules
| ID | Rule | Example / Detail |
| --- | --- | --- |
| BR-001 | ... | ... |

## 6. Validation Rules
| ID | Field / Action | Condition | Expected Behavior | Message |
| --- | --- | --- | --- | --- |
| VAL-001 | ... | ... | ... | ... |

## 7. UI And State Rules
| State | Trigger | Expected UI |
| --- | --- | --- |
| Loading | ... | ... |
| Empty | ... | ... |
| Error | ... | ... |
| Success | ... | ... |

## 8. Main User Flows
### Flow 1 - <Name>
1. ...
Expected result: ...

## 9. Abnormal And Edge Flows
| ID | Condition | Expected Behavior |
| --- | --- | --- |
| EDGE-001 | ... | ... |

## 10. Integrations / Side Effects
| Integration | Trigger | Expected Result | Failure Handling |
| --- | --- | --- | --- |
| ... | ... | ... | ... |

## 11. Notifications / Messages
| Trigger | Type | Audience | Message / Expected Text |
| --- | --- | --- | --- |
| ... | ... | ... | ... |

## 12. Traceability
| Source | Reference | Notes |
| --- | --- | --- |
| Jira | ... | ... |
| Spec | ... | ... |
| Code | ... | Inferred / confirmed |

## 13. Open Questions / Assumptions
| ID | Item | Impact | Owner |
| --- | --- | --- | --- |
| Q-001 | ... | ... | BA/PO |
```

## Step 7 - Save Or Return

If the user asked to save the QA spec, write it to the requested path.

If no path is provided, return it in chat only.

If saving inside this repository, prefer a tester-owned location such as:

- `tester/specs/<feature-id>-qa-spec.md`
- or a path explicitly provided by the user.

Do not edit official `spec.md`, `acceptance.md`, `tech.md`, or `meta.yml` unless the user explicitly asks and the repository rules allow it.

## Step 8 - Final Response

Summarize:

- what sources were used;
- where the QA spec was saved, if saved;
- any assumptions or unresolved questions;
- suggested next step: generate test cases with `/te-tester-gen-testcases`.
