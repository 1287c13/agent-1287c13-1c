# Roadmap & Release Planning

Read this when the user needs to communicate what's coming and when — to a team, a sponsor, or a customer. The recurring mistake is producing one artifact that tries to be both a direction and a promise, which makes it untrustworthy as the first and unachievable as the second.

## Contents
- Roadmap vs release plan
- Now / Next / Later
- Outcome-based cards
- Themes and the four lenses
- Communicating uncertainty
- Phased ERP rollout

## Roadmap vs release plan

| | Product roadmap | Release plan |
|---|---|---|
| Answers | **Why** this matters and **what** we're pursuing | **When** specific things ship |
| Contains | Outcomes, themes, problems, epics | Features, milestones, dependencies, dates, owners |
| Horizon | Quarters, continuously updated | 30/60/90 days, or 3–6 months for a major release |
| Nature | Direction and trade-off communication | A project plan |
| Commitment | Expected to change | The commitment; changes need renegotiation |

The line worth keeping: **the roadmap shows the plan; the OKRs carry the commitment.** That separation is what lets the roadmap stay honest. The clean chain is roadmap = why + what → release plan = when → engineering = how.

Timeline and Gantt roadmaps fail predictably: deadlines shift, morale drops from chronically missed commitments, the team turns into a feature factory optimizing output over outcome, and dates constrain discovery before anyone knows enough to commit. Apply dates only to genuinely time-critical items — a legal deadline, a contract, a partner launch, a fiscal-year cutover. Everything else lives in a horizon.

## Now / Next / Later

| Horizon | Meaning | Detail level |
|---|---|---|
| **Now** | Actively being built | Fully specified, with real confidence about scope and impact |
| **Next** | What we pick up once Now is done | Broken down less finely, fewer specifics |
| **Later** | The undefined future | Large blocks visible in the distance, deliberately not decomposed |

Uncertainty is communicated through **specificity**, not through a confidence percentage on a card: certainty is portioned out over time horizons, which gives you the chance to become more certain rather than committing too early. The structure itself encodes definite → probable → possible. Adding an explicit confidence label is a reasonable extension where stakeholders ask for one.

## Outcome-based cards

A feature roadmap removes the team's ability to find a better solution, because the solution is already written on the card. Prioritize at the problem level instead — the answer may turn out to be removing a feature, changing a price, or fixing a support process, and a feature roadmap forecloses all of those.

A card should carry: the **problem or opportunity** (not the feature) · the **segment** affected · the **outcome/metric** it should move and its link to a business objective · **confidence or stage** (discovery / validated / in build) · **current best-guess solutions, explicitly flagged as hypotheses** · a link to the evidence.

## Themes and the four lenses

**Themes** sit between strategy and items — a small number of durable, outcome-oriented groupings ("reduce time to first value", "make the product safe for regulated industries") that individual cards ladder into. They give the roadmap a narrative and let you show progress even when the underlying items change.

When generating candidates, brainstorm through four lenses and keep only what moves your input metrics. A roadmap drawn from a single lens is diagnosably unbalanced, which makes this a fast review heuristic:

| Lens | Source | Over-indexing risk |
|---|---|---|
| Strategy | Advances the product strategy | Users feel unheard |
| Vision | Progresses the long-term narrative | Neglects the existing core |
| Customer | Problems users explicitly raised | Feature bloat, power-user bias |
| Business | Improves the target metric's inputs | Underinvests in transformational work |

## Communicating uncertainty

- Use **different granularity per horizon** — the roadmap's shape should tell the truth about certainty.
- **Separate the documents explicitly**: roadmap changes, release plan and objectives don't change without renegotiation.
- **Name what would change the plan**, in the document: "we revisit this if the pilot fails / if the regulator publishes X / if activation doesn't move."
- **Show what came off** the roadmap and why. A roadmap that only ever grows trains people not to believe it.
- **Re-share on a cadence** (monthly), so change is routine rather than an event.
- **Give dates only where you can honour them** — and when you must give one far out, give a range with a confidence, never a single day.

## Phased ERP rollout

ERP and 1C implementations plan on a different axis from feature roadmaps, because the release unit is a *scope of business process going live*, not a feature. The recurring decision is the rollout pattern:

| Pattern | What it is | When it fits | What it costs |
|---|---|---|---|
| **Big bang** | Everything cuts over on one date | Small organization, one legal entity, a hard fiscal boundary | All risk lands on one weekend; rollback is painful |
| **Phased by function** | Accounting first, then warehouse, then production | Large scope, limited team | Temporary integrations between old and new, which are throwaway work |
| **Phased by site / entity** | One branch or company first, then the rest | Multi-site groups; lets you learn on a pilot | Two systems and two processes coexisting for months |
| **Parallel running** | Old and new processed together for a period | High-risk accounting scope, regulatory exposure | Double data entry — expensive and unpopular, so timebox it explicitly |

Whatever the pattern, the plan needs the things a feature roadmap never has: the **cutover date and its relationship to the accounting period** (a mid-month cutover usually costs more than it saves), the **opening balances** entry and reconciliation window, the **training** schedule relative to go-live (training more than three weeks early is forgotten), the **freeze** on configuration changes before cutover, and an explicit **rollback decision point** with the criteria that trigger it.

Pair the plan with a stabilization period after go-live — in 1C terminology usually ОПЭ, though the term's meaning varies by methodology, so pin it in the charter (see `1c-erp-analysis.md`) — whose exit criteria are conditions rather than a date: the period closes correctly, the defect backlog is below an agreed level, and named business owners sign off. Read `1c-erp-analysis.md` for the phase structure and acceptance artifacts that go with this.
