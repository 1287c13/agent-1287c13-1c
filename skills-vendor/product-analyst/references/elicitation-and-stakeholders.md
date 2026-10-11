# Elicitation, Stakeholders & Facilitation

Read this when the work is getting information out of people and keeping them aligned — interviews, workshops, conflicting demands, an executive request that arrived as a solution, or a "no" that has to be delivered without breaking the relationship. This is where most analysis projects actually fail, long before anyone writes a bad requirement.

## Contents
- Three modes of elicitation
- Choosing a technique
- The interview
- Running a requirements workshop
- The reluctant or busy stakeholder
- Stated need vs real need
- Five Whys, used properly
- Conflicting requirements
- Stakeholder mapping and RACI
- Saying no
- Handling an executive feature request
- Kickoff
- Decision log

## Three modes of elicitation

Collaborative (interviews, workshops, observation), research (document analysis, data mining, studying the existing system), and experiments (prototypes, pilots, controlled trials).

The rule that saves everyone's time: **never elicit from people what you can get from documents or data.** Do the research first, then bring findings to people for confirmation and gap-filling. This is the difference between a 30-minute interview and a three-hour one. Always sweep all three sources of requirements — stakeholders, documents, and the systems already in operation.

## Choosing a technique

| Technique | Use when | Yields | Main risk |
|---|---|---|---|
| Interview | You need depth, politics, exceptions, what really happens | Stakeholder requirements, tacit rules | They describe the ideal, not the actual |
| Workshop | Conflict must be surfaced and settled in one room | Agreed scope, a shared model, priorities | Dominated by the loudest voice |
| Document analysis | A legacy system, regulation or written procedure exists | AS-IS rules, data structures, terminology | Documents are stale; they describe intent, not practice |
| Observation / shadowing | The work is habitual or manual and they can't articulate it | Real workflow, workarounds, real volumes | Time-expensive; people behave differently while watched |
| Prototyping | Requirements are vague, or "I'll know it when I see it" | UI requirements, missing fields, validated flow | They mistake the prototype for the product |
| Survey | Many stakeholders, spread out, you need weight | Distribution of opinion, volumes | Can't probe; question bias |
| Interface analysis | Integration-heavy work — common in ERP | Interface inventory, data contracts, timing | Usually skipped until it's too late |
| Data analysis | You need real volumes and exception frequencies | Non-functional inputs, migration scope | Needs access |

## The interview

Six things to settle before you book it:

1. **Goal** — one sentence, written down. "Understand how credit limits are approved for new B2B customers today."
2. **Who** — pick by role coverage, not availability: the doer, the approver, the exception-handler, and the person who suffers the current process.
3. **Questions** — a prepared funnel: open → probing → closed → confirming.
4. **Logistics** — timebox, and at their desk if possible, because you get to observe. Recording consent. A second person to scribe if the content is dense.
5. **Flow** — open (purpose, timebox, what happens to this), body, close (read the summary back, agree next steps, ask who else you should talk to).
6. **Follow-up** — notes out within 24 hours with an explicit "reply by [date] or I'll take this as agreed."

A question funnel that works in practice:

- Context: "Walk me through what you did yesterday, from the moment this arrives."
- Volume: "How many of these a day? What's the peak?"
- Exception: "When does that *not* work? When did it last go wrong?"
- Rule: "Who decides? On what basis? What happens if they're away?"
- Pain: "If I could fix one thing here, what should it be?"
- Success: "Six months after go-live, what has to be true for you to say this was worth it?"
- Snowball: "Who else touches this? Who would disagree with what you just told me?"

Avoid leading questions ("you'd want an approval step here, right?"), design questions aimed at people who aren't designers ("should it be a button or a menu?"), and stacked questions. For discovery interviews about behaviour rather than process, `discovery-and-research.md` has the story-based technique, which is a stricter discipline than this funnel.

## Running a requirements workshop

**Roles:** sponsor (owns the outcome, opens the session, breaks deadlocks), facilitator (neutral — owns the process, not the content), scribe, timekeeper, participants, and optionally silent observers. Don't try to facilitate and be the domain expert at once; it biases the room.

**Before — this is 60% of the work.** A written objective with an explicit deliverable ("by 16:00 we have an agreed TO-BE order process and a ranked gap list"). Pre-interviews with two or three key participants so nothing is a surprise. A pre-read at least 48 hours ahead: AS-IS draft, glossary, open questions. And **bring a straw man, never a blank wall** — people critique far better than they create. Keep decision workshops to twelve people; five to seven is better.

**Agenda skeleton for a full day:**

| Time | Block |
|---|---|
| 0:00 | Sponsor opens: why we're here, what happens to the output, that today's decisions bind |
| 0:10 | Ground rules, agenda, parking lot |
| 0:20 | Context: scope diagram, glossary, AS-IS walkthrough of the straw man |
| 1:00 | Diverge: gather issues and pain — silent writing first, so nobody anchors the room |
| 2:00 | Converge: cluster, name, deduplicate |
| 3:00 | Model it live on the wall: TO-BE process, story map, decision table |
| 4:30 | Prioritize: MoSCoW, or dot-voting with a fixed vote budget |
| 5:30 | Confirm: read back decisions, assumptions and open items with owner and date |
| 6:00 | Close: what happens next, when they see the write-up, deadline for objections |

**Ground rules that earn their keep:** one conversation at a time; no laptops except the scribe's; "park it" is always available; absent means agreed; every open item leaves with an owner and a date; disagreement gets recorded rather than smoothed over.

Afterwards: minutes, decision log and open-items register within 24–48 hours, with a stated silence-means-consent deadline.

## The reluctant or busy stakeholder

Diagnose before you push — reluctance has different causes and opposite fixes.

| Cause | Signal | Fix |
|---|---|---|
| Genuinely no time | Cancels, one-line answers | Shrink the ask: 15 minutes, three questions, at their desk. Ask for *review*, not *creation* |
| Fears the project | Vague answers, "ask my manager", defensive | Address it openly and privately; get the sponsor to say publicly what happens to their role; find what the project gives them |
| Been burned before | "We did this two years ago and nothing happened" | Deliver a small visible win; show them their own words used in the last deliverable |
| Tacit knowledge | "I just know", "it depends" | Stop interviewing — observe, or work from concrete artifacts |
| Wrong person | Keeps deferring | Redo the stakeholder analysis |

Tactics that work on busy people: send a **deliberately incomplete or slightly wrong draft** and ask them to correct it, because correction is cheap and creation is expensive; hold **decision-only meetings** where the analysis went out in advance and their time is spent choosing between pre-analysed options; **piggyback on real work** by shadowing the actual month-end close instead of asking for a separate meeting; lead with an **artifact** — a real document they produced, or an actual stuck case pulled from their data ("this order sat four days — what happened here?"); take **one standing 30-minute slot a week** rather than chasing ad hoc; and escalate **the consequence, not the person** ("without a decision on the credit rule by Friday, sprint 7 ships the default behaviour and the rework costs about five days"). A deputy is acceptable for detail, never for scope or sign-off.

## Stated need vs real need

This is the core analytical skill. What a stakeholder states is almost always a solution they have already chosen.

The ladder: **solution asked for → requirement → need → problem → business goal.**

> Stated: "We need an Excel export button on the sales report."
> Requirement: sales managers must be able to analyse sales by custom dimensions.
> Need: they can't answer ad-hoc questions from the CEO without IT.
> Problem: the report has fixed dimensions and a two-week change cycle.
> Goal: cut decision latency in the weekly sales review.
>
> Real options: Excel export, *or* a self-service report builder, *or* three more standard filters. Only now can you choose — and only now is a cost comparison meaningful.

Ways to climb it: ask for the **trigger event** ("what happened the day you decided you needed this?") — the concrete incident is the real requirement; ask for the **current workaround** ("how do you cope today?") — the workaround *is* the specification; ask the **value question** ("if we build this, who does what differently, and how would we measure it?") — if nobody can answer, it's gold-plating; **reverse the ask** ("if we couldn't do that, what would you do instead?"), which often exposes a much cheaper fit; and require a **rationale** on every requirement, because a requirement with no rationale is a suspect.

## Five Whys, used properly

> **Problem:** about 30% of invoices are posted after the deadline.
> 1. Why? Accounting waits for warehouse confirmation.
> 2. Why? Confirmation is entered once a day, in the evening.
> 3. Why? The storekeeper types it up from paper notes after the shift.
> 4. Why? There's no terminal at the loading dock.
> 5. Why? The licence covers office workstations only.
> **Root cause:** licensing and hardware at the dock — not an accounting-process problem at all.

Four rules stop this producing nonsense. **Verify each link backwards with "therefore"** — if "the licence covers office workstations only, therefore the storekeeper types from notes after the shift" doesn't read true, the link is wrong. **Five isn't magic** — stop when you reach something you can change, and keep going if you haven't. **Branch** — real problems have two or three causal chains, and a single chain usually means you stopped thinking. And **stop before you reach a person**: "because Ivan is careless" is a failure of the method; ask instead why the process lets carelessness cause the failure.

## Conflicting requirements

Classify the conflict first, because the resolution depends entirely on the type:

| Type | Example | Resolution |
|---|---|---|
| Factual | Two people quote different VAT rules | Go to the source document. Never negotiate a fact |
| Terminology | "Order" means a quote to Sales, a confirmed order to the warehouse | Glossary and concept model. Most "conflicts" are this one in disguise |
| Interest | Sales wants speed, Finance wants credit control | A genuine trade-off — needs a decision-maker |
| Priority | Both want their module first | Prioritization framework plus sponsor |
| Constraint | Security wants MFA, Operations wants fast sign-on | Look for a technical option satisfying both |

Then: **document both positions and both rationales** in the decision log — never silently pick one. **Climb to needs**, because conflicting solutions frequently sit on top of compatible needs ("approve discounts automatically" vs "I approve every discount" both want *fast* and *controlled*; a threshold rule satisfies both). **Quantify the trade-off** in cost, risk and value rather than opinion. Apply an **agreed framework** so the outcome isn't personal. **Escalate with options, never with a problem** — bring the sponsor two or three pre-analysed choices, a recommendation and a deadline. **Record the decision, the rationale, and the losing position**, which is what kills the relitigation six months later. And **timebox**: an unresolved conflict past its SLA escalates automatically.

## Stakeholder mapping and RACI

**Power / interest grid:**

| | Low interest | High interest |
|---|---|---|
| **High power** | **Keep satisfied** — enough context that they don't become blockers; brief, high-signal updates; consult before anything that affects them | **Manage closely** — involve in discovery, co-own decisions, pre-brief before every major meeting, never surprise them |
| **Low power** | **Monitor** — minimum effort, re-check position periodically | **Keep informed** — regular detail; often your best allies and evidence sources |

Two attributes the classic grid omits and you need: each person's **stance** (champion / supportive / neutral / sceptical / blocker), and **what they care about** — their metric, their risk, their deadline — plus **how they decide** (data, narrative, a customer anecdote, peer consensus).

Two corollaries worth remembering. You can raise someone's *interest* far more easily than their *power*, which is how a high-power/low-interest risk becomes an ally. And a high-power sceptic must be consulted *before* your proposal is formed — consulting someone after the decision reads as notification and manufactures opposition.

Re-map every quarter, and always after a reorganization.

**RACI** — Responsible (does the work; at least one, keep it few) · Accountable (**exactly one**, owns the decision, and accountability is not delegated) · Consulted (two-way, keep the list short) · Informed (one-way, no response expected). Build it collaboratively rather than assigning unilaterally. Watch for: too many Consulted (slow, conflicting opinions), too many Responsible (nobody owns it), no Accountable (nobody decides), and rows with more than about five letters, which usually means the task is mis-scoped. For "who decides this" rather than "who does this", DACI or RAPID fit better.

## Saying no

The most powerful technique is to **let the system say no, not you**. When the roadmap, the objectives and the prioritization criteria are visible, a rejection is a system outcome rather than personal gatekeeping — and stakeholders start making the trade-off judgement themselves before they even ask.

For an inbound request: don't say no immediately — reflecting on it signals respect and buys thinking time. **Classify the no**: a hard no (conflicts with strategy) or a no-for-now (revisit later), and say which, because ambiguity here manufactures false hope and repeat requests. Back it with **evidence** rather than opinion. **Tailor it** — a CFO isn't moved by product metrics, so translate to business impact. Show empathy and probe for the underlying problem, since people are very good at asking for fixes that don't address their root problem and you'll often find something already planned that solves it another way. Then give **clear next steps**, with a timeframe if it's a no-for-now.

Two reframes that work better than refusal. **Redirect to the problem**: "help me understand what you'd be able to do if we had this" — then evaluate the *problem* against the opportunity space. And **trade-off instead of refusal**: "yes, and here's what comes out to make room" — putting the cost in the same sentence as the yes converts an argument with you into a decision for them. Log every significant no with its rationale; the same request returns in six months.

## Handling an executive feature request

1. **Never say no in the room.** "Let me understand it properly and come back to you Thursday."
2. **Convert the solution into a problem.** "What would be true if we had this?" "What are you seeing that makes this feel urgent?" Executives usually have real signal — a customer call, a board question, a competitor — attached to a bad solution. Take the signal, discard the solution.
3. **Look for the evidence, theirs and yours.** If the problem shows up in your data, they've given you a gift. If it doesn't, you now have a specific checkable disagreement rather than a status contest.
4. **Place it in the opportunity space**, not in the backlog, and show where it sits relative to current work.
5. **Present the trade-off, not the verdict.** "We can do this. It displaces X, which was projected to move [metric] by [amount]. Your call." Executives are paid to make trade-offs and usually make good ones when shown the real cost; the failure mode is a PM hiding the cost and just resisting.
6. **Offer the cheap test.** A one-week assumption test instead of a quarter of build turns "whose opinion wins" into "what will we know by Friday", which is almost always accepted.
7. **Escalate to the strategy, not the person**: "this changes our Q3 objective — should it?"
8. **Record the decision either way.** "Executive direction" is an honest rationale; writing it down keeps the team's model accurate and makes the pattern visible if it recurs.
9. **Close the loop.** An executive who gets a result and a follow-up is a much cheaper stakeholder next quarter.

## Kickoff

A 60-minute agenda, scaled proportionally for bigger projects: welcome and purpose (5) → business context (10) → goals and expected outcomes, with the metric and timeframe (10) → scope, deliverables, milestones **and non-goals** (10) → roles and collaboration model, walking the RACI (10) → risks, dependencies, open questions (10) → next steps with owners and dates (5).

Distribute the agenda and the document in advance, or open with silent reading if people won't pre-read.

**The kickoff isn't finished until all of these are true:** success criteria agreed in measurable terms · scope boundaries *and exclusions* confirmed · exactly one Accountable per workstream · milestones agreed · communication cadence set · escalation path defined · key risks identified with owners · cross-team dependencies mapped **and acknowledged by the other team** · immediate actions documented with dates.

## Decision log

The reason a decision was made evaporates within weeks. Without a record you relitigate quarterly and new joiners inherit conclusions with no context. Minutes capture the discussion; a decision log captures what was decided, why, and who approved it.

Log: strategic and prioritization decisions, resource and timeline trade-offs, architectural choices with long-term impact, anything cross-functional, risk and compliance decisions — and **every significant no**.

Fields: decision ID · date · type · one-sentence summary · decision-maker (one name) · stakeholders involved · **rationale and context** (the most important field) · alternatives considered · expected impact · status · review date · links.

For a weighty single decision, an ADR-style record works better than a table row: **context and problem statement · decision drivers · options considered · decision outcome with justification · consequences (good, bad, neutral) · how it will be confirmed**. Three product-specific fields are worth adding: **reversibility** (a two-way-door decision should be made fast and logged briefly), **what would change our mind** (which makes the decision falsifiable and the review date actionable), and **assumptions relied on**, linked back to the assumption map — so when an assumption is later disproven you can find every decision resting on it.
