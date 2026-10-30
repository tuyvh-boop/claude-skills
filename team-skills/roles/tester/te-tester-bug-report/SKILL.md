---
name: te-tester-bug-report
description: Generate a clear bug report from failed test evidence, expected behavior, actual behavior, logs, screenshots, or reproduction notes.
allowed-tools: AskUserQuestion, Bash, Read, Write, Edit, Glob, Grep
---

# /te-tester-bug-report

You are helping a tester write a high-quality bug report that a developer can reproduce and triage quickly.

The bug report must be factual, reproducible, and tied to expected behavior from source documents when available.

## Operating Principles

- Do not exaggerate severity.
- Do not assume root cause unless evidence proves it.
- Separate actual behavior, expected behavior, and suspected cause.
- Include exact data, environment, account/shop, browser/device, build/version, and timestamps when available.
- If expected behavior comes from a spec or test case, cite the source path or test ID.
- If evidence is incomplete, ask for the smallest missing detail that blocks reproduction.
- If the issue cannot be reproduced from the provided information, write a draft with "Needs more info" clearly marked.

## Step 1 - Understand The Bug Input

Use `$ARGUMENTS` as the initial clue. It may contain:

- failed test case ID;
- feature ID;
- bug title;
- Jira ticket;
- screenshot/log path;
- short reproduction notes.

Ask only for missing critical details:

1. What did you do?
2. What happened?
3. What did you expect?
4. Where did it happen: environment, shop/account, browser/device?
5. Is there evidence: screenshot, video, console log, network log, server log?

If the user has a failed test case file, read it first.

## Step 2 - Collect Context

Read relevant local sources when available:

- test case file;
- QA spec;
- official `spec.md`;
- `acceptance.md`;
- `tech.md`;
- `meta.yml`;
- related work order under `changes/`;
- screenshots/log text files provided by the user;
- standards: `.claude/rules/**` của repo hiện tại, if present

If this is an `optis-specs` feature ID, check:

- `app-swatch/features/<FEATURE_ID>/`
- `app-option/features/<FEATURE_ID>/`

Use source documents to determine expected behavior. If no source exists, state that expected behavior is based on tester observation or product expectation.

## Step 3 - Classify The Bug

Choose one or more classification values:

- Functional
- UI/UX
- Validation
- Permission
- Plan/Gating
- Integration
- API
- Data
- Performance
- Security
- Regression
- Compatibility
- Intermittent

Choose severity using impact:

- `Blocker`: prevents core flow, no workaround, release cannot proceed.
- `Critical`: major feature broken or data loss/security/payment issue.
- `Major`: important flow broken, workaround exists or impact limited.
- `Minor`: small functional/UI issue, low business impact.
- `Trivial`: typo/cosmetic with minimal impact.

Choose priority only if the team uses it. Otherwise omit or mark as "To be triaged".

## Step 4 - Reproduction Quality Checklist

Before writing final bug report, verify the report includes:

- environment;
- account/shop/user;
- build/version/branch if known;
- browser/device/OS if UI issue;
- preconditions;
- test data;
- exact reproduction steps;
- actual result;
- expected result;
- frequency;
- evidence;
- impact;
- source of expected behavior;
- workaround, if any.

If any item is unknown, use `Unknown` only when it is not critical. Ask the user if it blocks reproduction.

## Step 5 - Generate Bug Report

Use this default format:

```md
# Bug Report - <Short Title>

## Summary
<One sentence describing the defect and user impact.>

## Classification
- Type:
- Severity:
- Priority:
- Regression:
- Frequency:

## Environment
- App/Product:
- Environment:
- Build/Version/Branch:
- Shop/Account/User:
- Browser/Device/OS:
- Date/Time:

## Preconditions
- ...

## Test Data
| Field | Value |
| --- | --- |
| ... | ... |

## Steps To Reproduce
1. ...
2. ...
3. ...

## Actual Result
- ...

## Expected Result
- ...

## Evidence
- Screenshot:
- Video:
- Console log:
- Network/API:
- Server log:

## Impact
- User impact:
- Business impact:
- Scope:

## Source / Traceability
| Source | Reference | Expected Behavior |
| --- | --- | --- |
| Test case | ... | ... |
| Spec | ... | ... |
| Acceptance | ... | ... |

## Workaround
- ...

## Notes For Developer
- Reproducibility:
- Suspected area, if evidence supports it:
- Do not assume root cause without verification.
```

## Step 6 - Jira-Friendly Version

If the user asks for Jira format, output:

```md
*Summary*
...

*Environment*
- App/Product:
- Env:
- Build:
- Shop/User:
- Browser/Device:

*Preconditions*
- ...

*Steps to Reproduce*
# ...
# ...

*Actual Result*
...

*Expected Result*
...

*Evidence*
- ...

*Severity / Impact*
...

*Traceability*
- Failed test:
- Spec:
```

## Step 7 - Evidence Handling

When evidence is provided:

- Summarize logs instead of pasting huge logs.
- Include exact error messages if short.
- For network logs, capture endpoint, method, status code, request context, and response error.
- For screenshots/videos, describe the visible failure and reference the file path.
- For intermittent bugs, include number of attempts and pass/fail count.

## Step 8 - Duplicate / Regression Check

If the user provides existing bug IDs or related tickets, compare:

- same feature;
- same trigger;
- same actual result;
- same environment;
- same root symptom.

Mark as:

- New bug;
- Possible duplicate of `<ID>`;
- Regression of `<ID>`;
- Needs triage.

Do not mark duplicate unless evidence is strong.

## Step 9 - Save Or Return

If the user asks to save, write to the requested path.

If no path is provided, suggest:

- `tester/bugs/<feature-id>-<short-slug>.md`

Do not overwrite an existing bug report without reading it first.

## Step 10 - Final Response

Tell the user:

- bug title;
- severity recommendation;
- whether it is reproducible based on supplied info;
- missing information, if any;
- saved path, if saved.
