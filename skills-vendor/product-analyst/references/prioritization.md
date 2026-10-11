# Prioritization & Scope Negotiation

Read this when the user has more candidate work than capacity and needs an ordering they can defend. The frameworks below are decision *aids*, not decision *makers* — each one hides something, so pick deliberately and say out loud what it hides. A score you can't explain in a sentence is worse than an argued list.

## Contents
- Choosing a framework
- RICE
- ICE
- MoSCoW (and the effort rule everyone drops)
- Kano
- WSJF / Cost of Delay
- Opportunity scoring (importance vs satisfaction)
- Impact/Effort matrix
- Story mapping for release slicing
- Shape Up: appetite instead of estimate
- How to present a prioritization

## Choosing a framework

| Situation | Reach for |
|---|---|
| Many similar feature candidates in one product area, with real analytics | RICE |
| A long queue of cheap growth experiments, one scorer, speed matters | ICE |
| Fixed date and fixed budget, scope is the variable (most ERP go-lives) | MoSCoW |
| "Is this table stakes or a differentiator?" argued in a room with no data | Kano |
| Sequencing a queue of comparable items where delay has an economic cost | WSJF |
| A mature product; where to invest and where to *stop* investing | Opportunity scoring |
| Fast triage of a moderate list; you want the argument, not the number | Impact/Effort |
| Slicing a release so each slice works end to end | Story mapping |
| Fixed time, variable scope, a small team, no backlog | Shape Up appetite |

Three rules that hold across all of them. First, do not use a formula to choose which **problem** to work on — scoring belongs in the solution space, where the options are genuinely comparable. Second, never mix incomparable items on one scale (a security patch against a marketing feature produces a meaningless ordering). Third, a framework that never changes anyone's mind is theatre; if the ranking simply confirms what the loudest person wanted, say so.

## RICE

`RICE = (Reach × Impact × Confidence) ÷ Effort` — "total impact per time worked".

| Factor | Definition | Scale |
|---|---|---|
| Reach | How many people, in a defined period | A real count with units: customers/quarter, transactions/month — from analytics, not gut |
| Impact | How much per person | 3 massive · 2 high · 1 medium · 0.5 low · 0.25 minimal |
| Confidence | How sure you are of the above | 100% high · 80% medium · 50% low · below that it's a moonshot |
| Effort | Product + design + engineering | Person-months, whole numbers, minimum 0.5 |

Worked: 2,000 customers/quarter × impact 2 × confidence 0.8 ÷ 4 person-months = **800**.

**What it hides.** Multiplying an estimated Reach by a subjective Impact by a guessed Confidence produces three-digit authority built from three guesses. Large Effort in the denominator plus low Confidence on novel work systematically kills big bets and floats incremental tweaks to the top — so a team run purely on RICE never does anything strategically significant. Reach for a genuinely new product is unknowable, and the framework quietly turns "we don't know" into a number. It also ignores dependencies, sequencing and platform work whose reach is indirect. Intercom's own caveat stands: dependencies, commitments and strategy legitimately override the score; the score's value is that it makes you notice you are overriding it.

## ICE

`ICE = Impact × Confidence × Ease`, each 1–10. Note Ease is inverted effort, so it multiplies. Built for growth-experiment triage, not roadmap planning.

**What it hides.** There is no shared definition of what a 7 means, so two people produce contradictory rankings and the same person scores differently on different days. No unit anchoring at all — unlike RICE's person-months — so scores don't compare across teams or across time. Low Ease scores drag results down hard, which drifts a team into only doing easy things. And Impact/Confidence need business judgement while Ease needs technical knowledge; one scorer rarely has both.

## MoSCoW

Categories apply to **the current timebox**, not forever:

- **Must have** — the Minimum Usable SubseT. The test: *if the answer to "should we cancel the project rather than ship without this?" is yes, it's a Must.* Legal and safety requirements qualify.
- **Should have** — painful to omit, but a workaround exists and the solution still works.
- **Could have** — desirable, minimal impact if dropped. **This is your contingency pool.**
- **Won't have this time** — explicitly agreed out of *this* timeframe. Write it down; this is what stops scope creep.

**The effort rule, which is the entire mechanism:** Must ≤ **60%** of effort, Could ≈ **20%**, Should takes the rest. Above 60% Musts you are carrying real delivery risk unless estimates are accurate, the approach is proven and the team is settled.

**What it hides.** Without the percentage rule, everything becomes a Must and the framework tells you nothing — the labels alone are decoration. There is no ranking inside a bucket, so forty Shoulds still don't say what to build Monday. It carries no notion of value or cost, so it can't tell you whether the Musts are even worth doing. And teams read "Won't have" as "never", which poisons the negotiation; say "not in this release" every time.

## Kano

Two questions per feature, identical 5-point scale:
- **Functional:** "How would you feel if the product offered [feature]?"
- **Dysfunctional:** "How would you feel if the product did NOT offer [feature]?"

Response options, in this wording: *I would really like that · I expect that · I'm indifferent · I can tolerate that · I really dislike that.*

Evaluation table (row = functional answer, column = dysfunctional answer):

| ↓ functional / → dysfunctional | Really like | Expect | Indifferent | Tolerate | Really dislike |
|---|---|---|---|---|---|
| Really like | Q | A | A | A | O |
| Expect | R | I | I | I | M |
| Indifferent | R | I | I | I | M |
| Tolerate | R | I | I | I | M |
| Really dislike | R | R | R | R | Q |

*M = Must-be · O = One-dimensional (performance) · A = Attractive (delighter) · I = Indifferent · R = Reverse · Q = Questionable.*

**Categories and what to do:** Must-be — absence causes strong dissatisfaction, presence earns nothing; protect, never a differentiator. One-dimensional — satisfaction scales linearly; this is where you compete. Attractive — delights when present, costs nothing when absent; selective investment. Indifferent — don't build. Reverse — presence causes dissatisfaction; avoid, or segment.

**Analysis.** Discrete: take the modal category. Continuous (better): with Total = A + O + M + I, compute **Better = (A + O) / Total** and **Worse = −((O + M) / Total)**, then scatter Better against Worse. That preserves the distribution and lets you rank *within* a category.

**Sample size:** at least 30 responses per segment. A high Questionable rate is a defect in your question wording, not a confused respondent — anything above a few percent is worth rewriting for, and past about 10% the study is unusable.

**What it hides.** Attractive attributes decay into Must-be over time, so a study has a shelf life. It asks people to speculate about features they have never used — the same weakness that makes "would you use this?" useless in interviews — so it tells you about stated preference, not behaviour or willingness to pay. And it says nothing about cost, feasibility or strategy.

## WSJF / Cost of Delay

`WSJF = Cost of Delay ÷ Job Size`, where `CoD = User-Business Value + Time Criticality + Risk Reduction / Opportunity Enablement`.

- **User-Business Value** — direct economic benefit.
- **Time Criticality** — how fast the value decays. This is *urgency*, a different axis from importance. A regulatory deadline scores high; an evergreen improvement scores low even if it is hugely valuable.
- **RR|OE** — mitigates risk (tech debt, security, compliance) or unlocks future capability.
- **Job Size** — relative effort.

**The scoring mechanic is what makes it work:** modified Fibonacci (1, 2, 3, 5, 8, 13, 20), scored **one column at a time**. In each column find the smallest item, give it 1, and score everything else as a multiple of that. Never score a row across.

Note how every column below has a 1 in it — that is the anchoring rule applied, and it is what gives the scores their spread:

| Item | Value | Time crit. | RR/OE | CoD | Size | WSJF |
|---|---|---|---|---|---|---|
| Compliance update | 2 | 13 | 5 | 20 | 3 | **6.67** |
| Search performance | 1 | 3 | 2 | 6 | 1 | 6.00 |
| API integration | 5 | 3 | 5 | 13 | 3 | 4.33 |
| Analytics dashboard | 5 | 2 | 1 | 8 | 5 | 1.60 |
| Onboarding redesign | 8 | 1 | 3 | 12 | 8 | 1.50 |

**What it hides.** If your columns aren't anchored at 1, everything scores 8 or 13 and the method loses all discriminating power. Job Size is the denominator and therefore the easiest number to game. Adding three ordinal Fibonacci scores isn't mathematically meaningful, so treat the sum as a ranking device, not a quantity. Dependencies, learning value and option value are invisible — a discovery spike will always lose.

## Opportunity scoring (Ulwick)

`Opportunity = Importance + max(Importance − Satisfaction, 0)`

Survey **desired outcomes**, not features, on 1–10: how important is this outcome, and how satisfied are you with how it's delivered today. Sort descending.

- **> 15** — significantly underserved; the best innovation target.
- **10–15** — appropriately served; incremental.
- **< 10** — **overserved**; you are over-investing. Candidate for de-featuring or cost reduction.

That last band is the underrated output — almost no other framework tells you where to *stop* spending, and in an ERP context it is how you find the customizations nobody uses.

**What it hides.** It is only as good as your outcome statements; survey features instead of outcomes ("minimize the time it takes to…") and you have run a feature-request poll. Self-reported importance inflates — everything comes back 8+. New-to-world products have no satisfaction baseline to measure against.

## Impact/Effort matrix

| | Low effort | High effort |
|---|---|---|
| **High impact** | Quick wins — do now | Big bets — commit deliberately, after planning |
| **Low impact** | Fill-ins — for downtime | Money pits — avoid |

Define what "impact" and "effort" mean *before* anyone places a sticky, and place items together cross-functionally. The arguments about placement are the real output.

**What it hides.** It assumes items are independent, so dependencies vanish. Structurally it makes quick wins look strictly better than big bets, so a team run on this matrix alone never attempts anything significant.

## Story mapping for release slicing (Jeff Patton)

Three layers:
1. **Backbone** — user *activities* in narrative order (browse → choose → pay → track → receive). Test: each reads aloud as something a person does, not a screen or a feature. This test is what stops the map becoming a decomposed feature list.
2. **Tasks** — user-facing actions within each activity, still from the user's side.
3. **Details** — variations and edge cases, ordered vertically with the most necessary at the top of each column. That vertical order is what makes slicing possible.

**The crux:** a flat backlog gets cut **vertically** (top N by rank), which ships features that don't work together. A story map gets cut **horizontally across every column**, so each release spans the whole journey. The release line marks how *deep* you go, not how far. The thinnest slice that still works end to end is the **walking skeleton**.

Build the backbone as a group — the arguments about what comes before what surface fundamental disagreements about what the product is, which is the point. Then place existing stories under the activities (the gaps become obvious), order each column, and draw the release line **in the same session**. A map that is never sliced is decoration, and a "first slice" covering three of six activities is not a slice, it's a subset.

## Shape Up: appetite instead of estimate

Six-week cycle plus a two-week cool-down. **Appetite** — how much time we *want* to spend — replaces the estimate, which fixes time and makes scope the variable.

A **pitch** has five parts: **Problem** (a specific story, not an abstraction) · **Appetite** · **Solution** (rough, but solved and bounded — a problem with no solution isn't ready to bet on) · **Rabbit holes** (details called out to stop the team getting lost) · **No-gos** (explicitly excluded, to fit the appetite).

Other pieces worth borrowing even outside the full method: the **circuit breaker** (work that doesn't ship within its cycle is cancelled by default, not extended), **scope hammering** (cutting design aggressively to hit the date), **hill charts** (uphill = still figuring it out, downhill = executing — which separates "unknown" from "unfinished"), and no backlog at all, on the theory that important ideas come back.

## How to present a prioritization

In Georgian, always show these four things together. A bare ranked list invites "why is mine number seven?" and you will relitigate it every week.

```
## პრიორიტეტების ცხრილი     — the scored table, every input visible, not just the score
## რანჟირება და დასაბუთება   — the order, with one sentence per item on why
## რა რჩება მიღმა (Won't)     — explicitly out of this release/timebox, with the reason
## რას ვერ ხედავს ეს მეთოდი  — what this framework hides here (dependencies, strategy, big bets)
## დაშვებები                 — which numbers are measured and which are estimates
```

Mark every estimated input. If Reach is a guess rather than an analytics figure, write `[შეფასება]` next to it — the difference between a measured 2,000 and a guessed 2,000 is the whole credibility of the exercise.
