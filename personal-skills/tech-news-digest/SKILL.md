---
name: tech-news-digest
description: Use when the user asks for a roundup of recent tech/tool news ("cập nhật tin tech mới nhất", "có gì mới về AI/tool coding không", "tin tức công nghệ tuần này") — searches the web and produces a short, source-linked digest ranked by relevance to their stack. Not for deciding whether/how to adopt something in the codebase — that's a separate concern, not covered here.
---

# Tech News Digest

Produce a short, skimmable digest of recent tech news — not an exhaustive
dump. 2–3 items per category, one sentence each, always with a source link.

## Time window

Default to the **last 7 days** if the user doesn't specify one. If they say
"tháng này", "2 tuần qua", etc., use that instead — don't ask unless the
request is genuinely ambiguous.

## Categories, in priority order

Search and report in this order — higher-priority categories get filled
first, and if there's not much news, it's fine for a lower category to come
up short or be skipped entirely rather than padded with filler:

1. **Claude Code / Anthropic** — new Claude models, Claude Code features,
   Claude Agent SDK, MCP changes.
2. **AI coding tools** — other agentic coding tools, notable LLM releases
   relevant to software dev (Cursor, Copilot, competing models, etc.).
3. **Node.js / JS ecosystem** — Node.js releases, major framework/tooling
   changes (the user's backend stack).
4. **Shopify app dev** — Shopify API/platform changes, app dev tooling.

Use WebSearch per category (one or two targeted queries each — e.g. "Claude
Code changelog this week", "Node.js release notes <month>"). If the first
query returns too few solid items, one extra query on a related subtopic
(e.g. TypeScript/npm/Vite under the JS ecosystem category) is fine before
treating the category as genuinely thin. Skip a category outright only if
nothing credible turns up after that rather than stretching to fill it.

**Source quality:** prefer the primary/official source (nodejs.org,
shopify.dev, github.blog, code.claude.com/docs, vendor changelogs) over
aggregator or SEO-blog rewrites. If only an aggregator covers something,
still include it but note in the summary that the source is secondary and
worth verifying.

**Uncertain publish dates:** if a result looks relevant but you can't
confirm it falls inside the time window, include it anyway with a note on
the estimated date rather than silently dropping it — false negatives (news
the user never sees) are worse than a flagged maybe. This only applies when
the date is genuinely unknown — if a result has a confirmed date outside the
window, drop it; the window is a deliberate filter, not a soft suggestion.

**Cross-category duplicates:** if one story fits more than one category
(e.g. a coding-tool update that's also an Anthropic model release), put it
once under whichever category is more actionable for the user's actual
work — don't repeat it.

## Output format

Plain markdown in chat — no artifact needed for this length.

```
## <Category>
- **<Headline>** — <one-sentence summary, why it matters for this stack>. [source](<url>)
```

Order items within a category by relevance to the user's actual work
(OPTIS Shopify apps — Product Options, Color Swatch; Node.js/JS backend;
Claude Code + MCP workflow), not by recency or publisher prominence.

Skip categories with nothing found — don't print an empty heading.

If the user wants to know how any of this applies to their codebase, tell
them that's outside this skill's scope (no such skill exists yet to hand off
to — just say it needs separate follow-up).
