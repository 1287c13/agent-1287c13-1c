# Review Checklist

Use this when the user hands you an existing artifact and wants it critiqued rather than replaced — a PRD, a ТЗ or ЧТЗ, a requirements register, a backlog, a set of user stories, a process model, a roadmap, or an acceptance test plan. Reviewing is a distinct mode: you start from someone else's work, find what is wrong or risky, and report it constructively. Don't rewrite the document; show the specific defect and the specific fix.

## Review workflow

1. **Establish intent and audience first.** Restate in Georgian what this document is for, who signs it, and what decision it enables. A ТЗ judged as a PRD, or a PRD judged as a ТЗ, produces a review that is confidently wrong — see `srs-and-tz-standards.md` for the difference. Ask one focused question if the genre is genuinely unclear and it changes your judgement.
2. **Work the dimensions below in order.** Problem and outcome first, because a document that specifies the wrong thing precisely is worse than one that specifies the right thing loosely.
3. **Report by severity**, each finding with the offending text quoted and a concrete rewrite.
4. **Say what is done well**, briefly. Review is not only fault-finding, and it is what makes the criticism land.

Lead with the three or four findings that actually matter. An exhaustive flat list of forty items reads as noise and gets ignored wholesale, which is the worst possible outcome for a review.

## Severity levels

- 🔴 **კრიტიკული** — the document will cause the wrong thing to be built, or cannot be accepted against. Contradictory requirements, a missing acceptance basis, an invented business rule, a scope with no boundary.
- 🟠 **მნიშვნელოვანი** — a real gap that will cost time: an unverifiable requirement, a missing error path, an unowned open question, an untraceable requirement.
- 🟡 **მცირე** — clarity, terminology, structure, formatting.
- 🟢 **რეკომენდაცია** — an optional improvement or an alternative approach.

## Dimension 1 — Problem and outcome

- Is there a stated problem, or does the document open with a solution? A specification whose first section describes a screen has skipped the only question that matters.
- Is the problem **falsifiable and sized** — could somebody disagree with it, and does it carry a magnitude?
- Is there evidence, with a source, or an assertion presented as fact?
- Is there a **measurable outcome** with a baseline, a target and a date? "Improve efficiency" is not one.
- Does every requirement trace up to that outcome? A requirement supporting nothing is either a missing goal or gold-plating.
- Are **non-goals** stated, each with a reason? Their absence is the single best predictor of scope creep.

## Dimension 2 — Requirement quality

Run the nine characteristics from `requirements-engineering.md` over a sample, then over anything that looks suspicious: necessary · appropriate · unambiguous · complete · singular · feasible · verifiable · correct · conforming.

The fast scan that catches most of it:
- **Ambiguity words** — быстро, удобно, при необходимости, и т.д.; fast, user-friendly, as needed, etc. Every one is a defect.
- **Compound requirements** — "and" / "or" joining separate capabilities. If one half can pass while the other fails, they are two requirements.
- **Missing thresholds** — a number with no unit, a percentile, a volume or a condition.
- **TBDs with no owner and no date.** A TBD is an open item, not a requirement.
- **Error paths.** Walk the happy path and ask what happens when each step fails, times out, or receives invalid input. Prose specifications omit these almost universally; this is usually the richest seam in the whole review.
- **Non-functional requirements** — present at all? Each with metric, target, condition and measurement method? Sweep the categories so a whole class isn't missing.

## Dimension 3 — Completeness of the set

- **Contradictions** between sections, and between the text and the diagrams.
- **Uneven depth** — one feature specified to the field level, the next in one sentence. Usually a sign that the analyst stopped where their knowledge stopped.
- **Terminology** — is the same thing called by two names, or two things by one name? Is there a glossary? Most apparent requirement conflict is terminology conflict in disguise.
- **Roles and rights** — is there a permissions matrix, or is access described in prose (or not at all)?
- **Interfaces** — is there an inventory, with direction, format, trigger, frequency, matching rule and failure behaviour for each? An unlisted interface is an unpriced risk.
- **Transition requirements** — migration, opening balances, parallel running, training, cutover, decommissioning. Routinely 30–40% of ERP effort and routinely absent from the document.
- **Reporting** — which reports, for whom, and what decision is made from each.
- **Volumes** — does the document state the data volumes and concurrency the solution must hold at?

## Dimension 4 — Verifiability and acceptance

- Could an independent person take this document and decide, without asking the author, whether the delivered system complies?
- Does every requirement have a stated verification method, or at least an acceptance criterion?
- Are expected results **concrete** — numbers, statuses, register movements — rather than "works correctly"?
- Is there a control example with real data and a pre-computed expected answer? In accounting systems this is the only acceptance artifact that actually proves anything.
- Are the tests specified to run on realistic volumes?

## Dimension 5 — Stories and backlog (when reviewing a backlog)

- INVEST on a sample, especially **Valuable** (is this a task pretending to be a story?) and **Small**.
- A truthful `so that` on each — or is it "so that the system works"?
- Acceptance criteria present, testable, and agreed *before* development?
- Gherkin misuse: UI-coupled steps, conjunctions in one step, several rules per scenario, `Then` steps that act, performance requirements forced into Given/When/Then.
- Are epics decomposed, or is there an "epic" that has been in progress for four sprints?
- Is the Definition of Done carrying the cross-cutting requirements, or is each story silently re-deciding them?

## Dimension 6 — Models and diagrams

- Do the diagrams agree with the text? When they disagree, which one is authoritative — and does the document say?
- BPMN: tasks named with verbs, gateways labelled as questions, every path ending in an end event, message flow only between pools, exceptions as boundary events rather than extra branches. `process-modeling.md` has the full list.
- Is AS-IS mixed with TO-BE in one diagram, or are the two laid out differently so they can't be compared?
- Does every entity with a status field have a state diagram? A status field without one is a bug farm.
- Are multi-condition rules written as prose where a decision table belongs? Check the table's completeness: 2ⁿ combinations against the coverage.

## Dimension 7 — Prioritization and planning

- Is there a priority on every requirement, and does the priority mean something — or is 80% of the scope "Must"? If MoSCoW is used, check the effort split: Must ≤ 60%, Could ≈ 20%.
- Are estimates marked with their stage and accuracy, or presented as facts?
- Do the estimates include review, testing and rework, or only "development"?
- Is there a dependency or sequencing story, or a flat list?
- Does the roadmap conflate direction with commitment?

## Dimension 8 — 1C / ERP specifics

Apply these whenever the document targets a 1C or ERP implementation; `1c-erp-analysis.md` has the detail.

- **Fit-gap done at all?** Is each requirement judged against the standard configuration, or has the document assumed development from the start?
- **Was "change the process" considered** for each gap, and is the rejection reasoned?
- **Implementation level named per gap** — configuration, external object, extension, modification of a standard object, new object — and is the **support-mode consequence** stated? This is the total-cost-of-ownership question and it is the one most often missing.
- **Exact metadata paths** — or does the document say "the sales document"?
- **Attribute tables complete** — type with length and precision, mandatory and when it is checked, fill value, selection links, indexing, and the source of each value?
- **Posting described** — which registers, which dimensions and resources, which **sign**, and the formulas? And unposting, re-posting, and marking for deletion?
- **Period-close behaviour** and date boundaries specified?
- **Rights and RLS** stated as a matrix, including who must *not* see the data?
- **Exchange** — master of data named per entity, matching rule stated, behaviour on failure and on resend defined?
- **Migration** — reconciliation designed *before* the transfer, test waves planned, opening-balance check defined?
- **Extension risks** recorded where extensions are used — particularly that deleting an extension destroys the data stored in it?

## Reporting format

Report in Georgian, structured like this:

```
## შეფასების შეჯამება
2–4 sentences: what this document is, what state it's in, and the one thing
that would most improve it.

## 🔴 კრიტიკული
### 1. <short title>
**რა:** the quoted text or the missing section
**რატომ:** what will go wrong, concretely — at acceptance, in build, or in production
**როგორ:** the specific rewrite or the specific addition

## 🟠 მნიშვნელოვანი
…

## 🟡 მცირე
grouped, one line each — don't spend a paragraph on a naming inconsistency

## 🟢 რეკომენდაცია
…

## რა არის კარგად
2–3 specifics, not politeness
```

Two habits that make a review usable. **Quote before you judge** — a finding the author can't locate in their own document is a finding they will dismiss. And **write the fix, not the complaint**: "'the report shall be generated quickly' → 'the report shall render within 3 seconds at the 95th percentile with 5,000,000 records'" takes the same space as an explanation of why the original is bad, and costs the author nothing to accept.
