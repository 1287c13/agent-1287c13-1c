# Requirements Engineering

Read this whenever you are writing or auditing individual requirements — the sentence-level craft. A requirement that two people read differently is a defect that surfaces at acceptance, when it is at its most expensive.

## Contents
- The four levels of requirement
- The nine characteristics of a good requirement
- The "shall" sentence
- EARS — five sentence patterns
- Ambiguity words to avoid
- Writing non-functional requirements measurably
- Traceability
- Change, baselining and scope creep

## The four levels of requirement

| Level | Answers | Example |
|---|---|---|
| **Business** — goals and outcomes, enterprise-wide | *Why?* | "Reduce order-to-cash from 12 days to 7 by Q4." |
| **Stakeholder** — a need of one group; the bridge | *Who needs what?* | "The credit controller must see a customer's overdue balance before approving an order." |
| **Solution — functional** — behaviour and information | *What must it do?* | "The system shall block order confirmation when overdue balance exceeds the credit limit." |
| **Solution — non-functional** — qualities and conditions | *How well?* | "The credit check shall return within 2 s at the 95th percentile with 50 concurrent users." |
| **Transition** — capabilities needed to get from current to future state; temporary | *How do we get there?* | "Migrate 5 years of open AR balances with a reconciliation report showing zero variance." |

**Transition requirements are the ones everyone forgets**, and in ERP work they are routinely 30–40% of the effort: data migration and cleansing, parallel running, opening balances, cutover, training, temporary integrations, access to historical data, and decommissioning the old system. They can't be derived until both the current and future states are described, which is why they arrive late — plan for them anyway, and put them in the document as a named section so the budget conversation happens early.

## The nine characteristics of a good requirement

From ISO/IEC/IEEE 29148. Use this as the audit checklist in review mode.

**1. Necessary** — remove it and a real gap appears.
> ✗ "The system shall use a three-tier architecture." (a design decision nobody asked for)
> ✓ "The system shall support 500 concurrent users with no single point of failure in the application layer."

**2. Appropriate** — at the right level of abstraction for this document, not over-constraining the implementer.
> ✗ (in a business document) "The customer table shall have a VARCHAR(50) name column."
> ✓ "The system shall store a customer's legal name as recorded in the state register."

**3. Unambiguous** — one and only one reading.
> ✗ "The report shall be generated quickly and show recent orders."
> ✓ "The Orders report shall render within 3 seconds and list all orders with a document date in the preceding 30 calendar days."

**4. Complete** — no further amplification needed; all conditions and thresholds stated; no TBDs.
> ✗ "The system shall notify the manager of overdue invoices."
> ✓ "When an invoice reaches 5 calendar days past its due date, the system shall send an email to the customer's assigned account manager containing the customer name, invoice number, due date and outstanding amount."

**5. Singular** — exactly one requirement. The test: *can one part pass while another fails?* Then they are separate.
> ✗ "The system shall validate the tax ID, store the customer record, and send a welcome email." → three requirements.

**6. Feasible** — achievable within known cost, schedule, technology and law.
> ✗ "…detect fraudulent transactions with 100% accuracy."
> ✓ "…flag for manual review any transaction scoring ≥ 0.8 on the fraud model, achieving ≥ 95% recall on the validation dataset."

**7. Verifiable** — there is a finite, affordable way to prove it: inspection, analysis, demonstration or test.
> ✗ "The interface shall be intuitive and user-friendly."
> ✓ "A user who has completed the 30-minute onboarding shall create a sales order in ≤ 90 seconds, median over 10 test users, with ≥ 90% task success."

**8. Correct** — it represents the actual stakeholder need, not the analyst's assumption.
> ✗ "The system shall archive documents older than 1 year."
> ✓ "The system shall move accounting documents to the archive 5 years after their document date, per the retention policy in Regulation X §4.2."

**9. Conforming** — follows the document's template, terminology and standard.

For the **set** as a whole, five more: complete (no gaps), consistent (no contradictions, uniform terminology), feasible collectively (individually achievable items can be jointly impossible), comprehensible (structured, not a flat list of 800 lines), and able to be validated by stakeholders. Add **prioritized** as an attribute of every requirement even though the standard dropped it from the individual list — an unprioritized set cannot be scope-managed.

## The "shall" sentence

```
[Condition] the <subject / system name> shall <action> <object> [qualifier].
```

- **Exactly one `shall`** per requirement. `shall` = binding · `should` = desirable, non-binding · `will` = a statement of fact about the environment · `may` = permission. Don't mix `must` and `shall` in one document; pick one and define it in the glossary.
- **Name the subject.** "The system" is fine only when there is exactly one system. In an integration project, name the component: "The Billing subsystem shall…".
- **Active voice.** "The invoice shall be validated" — by whom?
- **Positive form** where equivalent: "shall reject" beats "shall not accept", because negatives are harder to test and often unbounded.
- **One sentence.** If you need a second, you probably have a second requirement — or the extra sentence is rationale, which belongs in a Rationale attribute.

## EARS — five sentence patterns

Constraining the sentence shape removes most ambiguity mechanically. Keyword order is fixed: `WHERE → WHILE → WHEN/IF`.

**1. Ubiquitous** — always active.
`The <system> shall <response>.`
> The Order subsystem shall store the user ID of the person who created each order.

**2. Event-driven** — a discrete trigger.
`WHEN <trigger>, the <system> shall <response>.`
> WHEN an order is confirmed, the Order subsystem shall reserve the ordered quantity in the warehouse.

**3. State-driven** — active while a state holds.
`WHILE <state>, the <system> shall <response>.`
> WHILE the accounting period is closed, the Accounting subsystem shall reject posting of documents dated within that period.

**4. Optional feature** — only in configurations that include it.
`WHERE <feature is included>, the <system> shall <response>.`
> WHERE the EDI module is licensed, the Order subsystem shall accept ORDERS messages in EDIFACT D.96A.

**5. Unwanted behaviour** — errors, failures, invalid input.
`IF <unwanted condition>, THEN the <system> shall <response>.`
> IF the credit-limit service does not respond within 5 seconds, THEN the Order subsystem shall queue the order with status "Pending credit check" and notify the credit controller.

**Complex** — combine, in keyword order.
> WHERE the multi-company option is enabled, WHILE the session company is set, WHEN a new document is created, the system shall default the document's company to the session company.

Two reasons this is worth the discipline. The **unwanted-behaviour pattern forces you to enumerate error paths** that prose specifications silently omit — which is exactly where ERP projects bleed during acceptance. And the patterns map almost one-to-one onto Gherkin (`WHILE` → Given, `WHEN` → When, `shall` → Then), so writing requirements this way makes the acceptance criteria nearly free.

## Ambiguity words to avoid

| Word | Why it fails | Write instead |
|---|---|---|
| acceptable, adequate, sufficient | Whose judgement? | Define what qualifies and how the system decides |
| efficient, flexible, robust, scalable | Unmeasurable | Specify throughput, what must be changeable and by whom, behaviour under failure, the growth multiple |
| user-friendly, easy, intuitive, seamless | Unverifiable marketing | Task time, error rate, training time |
| fast, quick, real-time, instantaneous | Unverifiable | A time budget with a percentile |
| improved, better, faster | Relative to what? | "from 8 s to ≤ 3 s" |
| including, etc., and so on | Open-ended — can't be designed or tested | Enumerate exhaustively |
| maximize, minimize, optimize | No target | State the acceptable range |
| at least / not more than (alone) | Half a bound | Give both bounds |
| between | Endpoints included? | "from 1 to 10 inclusive" |
| normally, ideally | Only the happy path | Specify the abnormal case too |
| optionally | Whose option? | Say who chooses — system, user or developer |
| reasonable, where appropriate, if needed | Hides the criteria | State the criteria |
| several, some, many | Unquantified | Give the number or a bounded range |
| support, handle, manage, process | Hides the actual behaviour | Name the functions performed |
| and / or joining capabilities | Compound requirement | Split into singular requirements |
| TBD | Not a requirement | Assign an owner and a closure date; track it as an open item |

In Georgian output the same discipline applies — "მოსახერხებელი", "სწრაფი", "საჭიროებისამებრ" and "და ა.შ." are exactly as unverifiable as their English equivalents. When the source material genuinely doesn't contain the number, write the requirement with an explicit `[დასაზუსტებელია: <what is missing>, <who can answer>]` rather than inventing a threshold. An invented threshold reads as authoritative and nobody ever questions it again.

## Writing non-functional requirements measurably

```
<quality> of <component> shall be <metric> <operator> <value>
under <conditions>, measured by <method>.
```

Every NFR needs four parts: **metric + target + condition + measurement method**. Miss one and it is unverifiable.

Sweep the ISO/IEC 25010 categories so you don't forget one: functional suitability · performance efficiency · compatibility · interaction capability (usability) · reliability · security · maintainability · flexibility (adaptability, scalability, installability, replaceability, testability) · safety.

**Performance** — always state response time vs throughput vs capacity, the percentile (never the mean alone), the data volume, the concurrency, and whether client rendering counts.
> "The Order List screen shall render within 2.0 s at the 95th percentile with 200 concurrent users and 5,000,000 order records, measured server-side excluding network latency."
> "The nightly close shall process 1,000,000 postings within 4 hours on the reference hardware in Annex B."

**Availability** — state the measurement window and what counts as "down", or the number means nothing.
> "The order-entry service shall achieve 99.5% availability measured monthly during 08:00–20:00 Tbilisi time, excluding the planned Sunday 02:00–05:00 window. Unavailable = 3 consecutive failed synthetic transactions at 1-minute intervals. RTO ≤ 4 hours; RPO ≤ 15 minutes."

Downtime per month (30.44-day month): 99% = 7h18m · 99.5% = 3h39m · 99.9% = 44m · 99.95% = 22m · 99.99% = 4m23s. Quote these when a sponsor asks for 99.99% without knowing what they're buying.

**Security** — name the control, the threat, the standard clause and the verification.
> "All data in transit shall use TLS 1.3 or higher; TLS 1.2 and below shall be rejected. Verified by quarterly external scan."
> "The system shall record an immutable audit entry — user ID, UTC timestamp, object type, object ID, old value, new value — for every create, update and delete of a Customer, Price or Credit Limit record. Readable by the Auditor role; modifiable by no role."
> "After 5 failed authentication attempts within 15 minutes the account shall be locked for 30 minutes and the security mailbox notified."

Express access control as a **roles-and-permissions matrix**, never as prose.

**Usability**
> "A new warehouse operator, after the 30-minute onboarding video, shall complete a 10-line goods receipt in ≤ 3 minutes (median over 10 users) with ≥ 90% first-attempt success."
> "The system shall support Georgian, Russian and English interface languages; all user-visible strings shall be externalised, with no literals in code."

That last one matters in 1C work specifically: it is the requirement that makes `НСтр()` mandatory rather than optional, and it is cheap at design time and expensive later.

**Compliance** — cite the instrument and the clause. Never write "shall comply with all applicable legislation"; it is unbounded and unverifiable.
> "Invoices shall contain all attributes required by [Tax Code Art. X] and shall be transmitted to the Revenue Service e-invoicing endpoint within 1 business day of posting."

**Retention** — specify separately the period, the trigger (creation / last activity / contract end), the destination (archive, anonymise, delete), accessibility in each phase, who may trigger early deletion, and legal-hold exceptions.
> "Accounting documents shall be retained online for 5 years from document date, then moved to the archive where they remain queryable read-only for a further 5 years, then permanently deleted. Deletion shall be logged."

**Operational NFRs**, routinely forgotten in ERP:
> "The system shall support growth to 3× current transaction volume (today 12,000 documents/day) without architectural change."
> "A full production restore shall complete within 6 hours; the procedure shall be tested quarterly."
> "Unattended downtime for a version upgrade shall not exceed 4 hours, executable within a Sunday maintenance window."

That last one is the requirement that decides whether a 1C configuration can be customized directly or must stay on support with extensions — see `1c-erp-analysis.md`.

## Traceability

A traceability matrix exists so that when something changes you can answer "what else does this touch?" without reading everything. Minimum useful columns:

| Req ID | Requirement | Source (who/where) | Priority | Business goal | Design / object | Test case | Status |
|---|---|---|---|---|---|---|---|

Trace **upward** to the business goal (a requirement tracing to nothing is a candidate for deletion), **downward** to the design or metadata object that implements it, and **across** to the test case or acceptance scenario that proves it. In a 1C project the "design/object" column is where the requirement meets reality: name the справочник, документ, регистр, отчёт, роль or обмен that carries it. A requirement with an empty object column at the end of design is either missed or unnecessary, and either answer is worth knowing.

Keep it proportionate. Full bidirectional tracing on a two-week change is bureaucracy; on a regulated ERP implementation it's what lets you answer an auditor.

## Change, baselining and scope creep

**Baseline** the requirement set at an agreed version and date, and from that point change goes through an explicit path. A baseline nobody can name is the same as no baseline.

**Impact analysis** for a proposed change, in this order: which requirements does it touch (use the matrix) → which design and metadata objects → which test cases → which already-completed work is invalidated → what does it cost in effort, schedule and risk → who decides. Present all six; a change request answered with only a cost estimate invites "just do it".

**Scope creep** is not the same as legitimate change. The distinction worth holding: a *change* is a decision made with its cost visible; *creep* is a change that entered without one. The defences are all procedural — a written baseline, non-goals stated up front, every new ask routed through the same estimate-and-decide path regardless of who asks, and a visible record of what was added and what came out to make room. When a requirement arrives mid-build, the useful response is never "no" or "yes" but "here is what it costs and here is what it displaces."
