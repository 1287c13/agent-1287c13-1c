# PRD & Product Spec Writing

Read this when the deliverable is a product document — a brief, a PRD, a one-pager, a PR/FAQ. For a formal requirements specification (SRS / ТЗ / ГОСТ), read `srs-and-tz-standards.md` instead; the two are different genres and mixing them produces a document that satisfies nobody.

## Contents
- Sequence: why documents fail
- The three stages of a product document
- Recommended PRD section list
- Writing the problem statement
- Non-goals and out of scope
- Linking requirements to success metrics
- Amazon PR/FAQ
- The one-pager
- Length discipline

## Sequence: why documents fail

The common complaint that "PRDs are dead" is really a complaint about sequence, not about artifacts. A document written *instead of* discovery is the problem; a document written *after* discovery, as an implementation and QA reference, is a reasonable tax — especially for a distributed team, and doubly so for an ERP project where the document is also a contract.

What a prototype does that a document cannot: it enables give-and-take between product, design and engineering instead of a sequential handoff; it lets you test value, usability, feasibility and viability before production code; you can put it in front of users; and stakeholders react to it honestly. So where a prototype or a mockup is possible, the prototype is the authoritative description of the experience and the document describes the rules, the edge cases and the acceptance criteria around it.

The practical rule: write the **problem-space** document to align on what problem and why, *before* solutioning. Use prototypes and models as the solution artifact *during* discovery. Write the **detailed spec** *after* discovery, for build and acceptance.

## The three stages of a product document

Each stage matches a decision, so don't write stage 3 when the organization hasn't made the stage 1 decision.

**Stage 1 — Product brief (problem space).** Aligns leadership on whether solving this is worth it. Contains: the opportunity (problem, audience, why now), supporting evidence, success metrics, and non-goals. One page.

**Stage 2 — Product spec (solution space).** Aligns cross-functional leads on the approach. Adds: scope as user stories and functional requirements split must-have / nice-to-have, the user flow, and the risks and open questions still to be pressure-tested. Two to four pages.

**Stage 3 — Full PRD (execution).** Enables building. Adds: technical implications and instrumentation, rollout and go-to-market plan, and the development plan with owners and dates. This is a reference document, not a read-through.

Two failure modes sit on either side of this. **Overthinking** — dissertation-length documents chasing completeness — is usually a symptom of a trust or ownership problem rather than a documentation problem, and more pages won't fix it. **Under-documenting** — treating the document as a barrier to progress — pushes unresolved questions downstream where they are far more expensive. Both come from treating the document as a process tool for managing people rather than as a thinking aid.

## Recommended PRD section list

Sections marked ○ are optional for a small change.

| # | Section | What belongs in it |
|---|---|---|
| 1 | Title, author, DRI, status, date, reviewers | Status is Draft / In review / Approved / In build / Shipped / Abandoned, so a reader knows how much to trust it |
| 2 | TL;DR (≤5 sentences) | What, for whom, why now, what success looks like — written so an executive can stop here |
| 3 | Problem statement | The customer's problem in the customer's terms, with evidence, size and cost. No solution language |
| 4 | Evidence | Interview quotes, ticket volumes, analytics, competitive data — with links, so §3 is checkable |
| 5 | Target customer / audience | The specific segment and the situation they're in |
| 6 | Goals / desired outcome | The behaviour change, as an objective plus the metric that moves |
| 7 | Non-goals / out of scope | What we are explicitly not doing, why, and what that costs |
| 8 | Success metrics | Primary metric with target and timeframe, supporting metrics, and guardrails that must not degrade |
| 9 | Solution overview | The approach in prose plus a link to the prototype or mockups |
| 10 | User flows / key scenarios | Happy path plus named edge cases |
| 11 | Requirements | Numbered, testable, tagged Must/Should/Could, each traceable to a goal |
| 12 | ○ Design | Link to mocks; what is settled vs still exploring |
| 13 | ○ Technical considerations | Architecture, dependencies, data model, instrumentation, migration |
| 14 | Assumptions & risks | The riskiest assumptions and how each was or will be tested |
| 15 | ○ Rollout plan | Phases, exposure, kill criteria, what triggers rollback |
| 16 | ○ GTM / launch | Comms, docs, support enablement, pricing, training |
| 17 | Open questions | Question, owner, date needed — an open question with no owner isn't tracked |
| 18 | Decision log | Dated: what was decided, alternatives, why, who decided |
| 19 | ○ Appendix | Research, prior docs, raw data |

## Writing the problem statement

Fill all five parts, in order: **who** (a specific segment, not "users") · **what** (the situation and the struggle, in their language) · **evidence** (how we know) · **impact** (what it costs them and what it costs us) · **why now** (what changed, or the cost of inaction).

> **[Segment]** trying to **[achieve outcome]** currently **[what they do today]**, which causes **[specific struggle]**. We know this because **[N interviews / X% of tickets / Y% drop-off at step Z]**. This costs them **[time/money/risk]** and costs us **[metric impact]**. It matters now because **[trigger]**.

Four rules make the difference between a problem statement and a wish:

- **No solution in it.** If you can delete a noun and the sentence still makes sense, that noun was a solution. "Users need a bulk export button" → "Users spend 40 minutes re-keying data one record at a time."
- **Falsifiable.** Somebody has to be able to disagree with it. "Users want a better experience" cannot be wrong, and is therefore useless.
- **Sized.** Without a magnitude it can't be prioritized against anything.
- **In the customer's words**, ideally lifted verbatim from an interview.

Keep the **business problem** ("churn in segment X is 4 points above plan") and the **customer problem** ("when X happens, customers can't Y") as separate sentences, and connect them. A document with only the first reads as management pressure; with only the second, as advocacy without a business case.

## Non-goals and out of scope

Non-goals are the cheapest scope control in the document: they turn an argument you would have in week four into a sentence you write in week zero, and they tell engineers what *not* to design for, which is often more load-bearing than what to design for.

Three kinds, and they read very differently — label which one you mean:

1. **Out of scope this release** — real, wanted, deferred. "Not in v1; tracked as [link]."
2. **Anti-goal** — deliberately not doing, possibly ever, because it conflicts with the strategy. "We will not support X, because it would require Y, which contradicts Z."
3. **Not-a-goal** — a plausible objective this project isn't trying to move, so nobody measures us on it. "This project is not intended to improve [metric]."

Phrase each as `[the thing] — because [reason] — [consequence / where it goes instead]`. The "because" is not optional; a bare list of non-goals reads as arbitrary and gets relitigated. Then answer the second question too: given we're not solving these, how does that change our chance of success? That forces you to state the risk you are accepting.

The best non-goals are the ideas that *almost* made it — harvest them from the rejected brainstorm, from Shape Up's "no-gos", and from MoSCoW's "won't have this time".

## Linking requirements to success metrics

This is a mechanism, not a sentiment:

1. **One primary metric per document.** Three primary metrics means none.
2. Write the metric as **metric + direction + magnitude + timeframe + population**: "increase 7-day activation from 34% to 40% for new self-serve signups within 60 days of GA." All five parts.
3. **Number every requirement** (R1, R2…).
4. Add a **Supports** column mapping each requirement to a goal or metric. A requirement that supports nothing is a candidate for non-goals; a metric with no requirement pointing at it is unresourced.
5. Name the **instrumentation** per requirement — the event and its properties. If a requirement's success can't be observed, it isn't done.
6. Declare **guardrails** alongside the primary metric, with the threshold that halts rollout.
7. **Pre-register the decision rule**: "if the primary metric moves ≥ X and no guardrail degrades more than Y, we go to 100%; otherwise we [roll back / iterate / stop]" — written before launch, not after the data arrives.

| ID | Requirement | Priority | Supports | Instrumented by |
|---|---|---|---|---|
| R1 | User can import a CSV of up to 10,000 rows | Must | G1 / activation | `import_completed{rows, duration}` |
| R2 | Import errors show the offending row number | Should | G1 (reduce abandonment) | `import_error{type, row}` |
| R3 | Import history retained 90 days | Could | — | — → move to non-goals |

In an ERP context the instrumentation column is often a report or a register rather than an analytics event — name it anyway ("verified via the Остатки по складам report for period X"), because the point is that someone can check.

## Amazon PR/FAQ (working backwards)

Write the launch announcement first, as a forcing function for customer focus.

**Press release, in order:** heading (one sentence naming the product for its customers) · subheading (the segment and the benefit) · summary paragraph · problem paragraph, from the customer's side · solution paragraph · two quotes, one from the company and one from a hypothetical customer · getting started.

**External FAQ:** price, how it works, support, where to get it.

**Internal FAQ** — where the real work is: how do customers solve this today; what value is created and for whom; competitive differentiation; market size; capabilities and third-party dependencies; technical, legal and operational challenges; unit economics and payback; critical assumptions; and **the top three reasons this product will not succeed** — the single highest-value question in the format.

**The review meeting:** circulate at the start, 15–20 minutes of silent reading with comments written into the document, then about 40 minutes of discussion. Expect many revisions over weeks or months.

Use this format when the idea is genuinely new and the risk is that nobody wants it. Don't use it for an increment to an existing system — the press release becomes a parody of itself.

## The one-pager

Six questions, nothing else. Good for a request that arrives half-formed, and good as stage 1 when a full brief would be over-ceremony:

1. **Description** — what is it?
2. **Problem** — what problem does this solve?
3. **Why** — how do we know it's real and worth solving?
4. **Success** — how will we know we solved it?
5. **Audience** — who are we building for?
6. **What** — what does this look like in the product?

## Length discipline

One page at stage 1; two to four at stage 2; stage 3 is a reference. Any section nobody has ever read should be deleted. When in doubt, cut the prose and keep the tables — requirements, metrics, open questions and decisions are what people come back to.
