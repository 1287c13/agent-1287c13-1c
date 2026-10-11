# User Stories & Acceptance Criteria

Read this when the deliverable is a backlog: epics, features, stories, acceptance criteria, Definition of Ready and Done. The recurring failure here is a story that reads fine and means three different things to the three people who read it, which surfaces as rework in the last week of the sprint.

## Contents
- The three C's
- Story format
- INVEST
- Splitting a story: nine patterns
- Story mapping
- The hierarchy: theme → epic → feature → story
- Definition of Ready / Definition of Done
- Acceptance criteria: rules vs scenarios
- Gherkin, and how it goes wrong
- Specification by example
- Acceptance criteria for ERP work

## The three C's

| C | What it is | What breaks without it |
|---|---|---|
| **Card** | A short written token, deliberately too small to hold the whole specification. Its job is to be a promise to have a conversation and a planning handle | The card is treated as the spec, and the team builds from a one-liner |
| **Conversation** | The actual requirement — an ongoing dialogue between the business, developers and testers, mostly verbal, supported by sketches and examples | The card gets interpreted three different ways |
| **Confirmation** | The acceptance criteria, agreed *before* development starts | Endless "is it done?" and rework |

If you only remember one thing: the story is not the requirement. The conversation is the requirement, and the acceptance criteria are its residue.

## Story format

```
As a <role>,
I want <capability>,
so that <benefit>.
```

The `so that` clause is not decoration — it is the rationale, and it is how you tell a real story from a task in disguise. If you can't write a truthful `so that`, question whether the story should exist at all.

The **job story** variant — `When <situation>, I want to <motivation>, so I can <expected outcome>` — is often better in back-office and ERP work, where the trigger context matters more than the job title and where "as a user" has become meaningless because everyone is a user.

## INVEST

| Letter | Test | Fix when it fails |
|---|---|---|
| **Independent** | "Could we do this alone, next sprint, without story X?" | Combine the two, or split differently — by workflow step rather than by layer |
| **Negotiable** | "Does the card prescribe the UI or the implementation?" | Move solution detail into the conversation; keep intent on the card |
| **Valuable** | "Could I demo this to a business person and have them care?" | Re-slice vertically. A story ending at a layer boundary ("build the data access object") is a task |
| **Estimable** | "Can the team give a number without shrugging?" | Clarify, split, or run a spike |
| **Small** | A few days; six to ten fit a sprint by the time they reach the top | Split — see below. "More than a month" usually means "I don't understand what this entails" |
| **Testable** | "Can I state a pass/fail condition?" | Usually a missing fit criterion on a non-functional aspect |

## Splitting a story: nine patterns

The entry condition: the story already satisfies INVEST *except* Small, and delivers visible incremental value. If it doesn't, splitting isn't the problem — you have a task or a technical chore.

| # | Pattern | Example |
|---|---|---|
| 1 | **Workflow steps** — build the simplest path through the flow first | Publish a news item without review → add editorial review → add legal review |
| 2 | **Business rule variations** — one rule set at a time | Exact date search → ±3 days → weekend → date range |
| 3 | **Major effort** — several similar things where most cost is in the first | Pay by VISA → add Mastercard → add Amex |
| 4 | **Simple / complex** — extract the simplest version, defer variations | Basic search → max stops → nearby airports |
| 5 | **Data variations** — same behaviour, different data scope | Search by region → by city → by custom service area |
| 6 | **Data entry methods** — same function, richer input later | Type a date → add a calendar picker |
| 7 | **Defer performance** — make it work, then make it fast | Results with a spinner → optimise to ≤ 1 s |
| 8 | **Operations (CRUD)** — split "manage X" into operations | Sign up → edit settings → cancel |
| 9 | **Break out a spike** — a timeboxed question with a required output | "Can we call the bank API with our certificate? 1 day. Output: yes/no plus the integration approach" |

The meta-pattern: **find the complexity, then reduce the variations.** Locate the single hardest thing — usually human judgement or an external dependency — and carve one complete slice that goes all the way through it.

When choosing between candidate splits, prefer the one that lets you **drop or deprioritise** the low-value part, and prefer splits producing **roughly equal-sized** stories over a lopsided one.

A good split is never horizontal (database layer / service layer / interface layer). A vertical slice changes system behaviour in a way a business person can see, and it usually touches several layers to do it.

For a stubborn story, the **hamburger method**: list the workflow steps as layers, brainstorm three to five quality options per layer from crudest to richest, pick one option per layer to define the thinnest acceptable version, and improve layers in later stories.

## Story mapping

```
            ------------ narrative flow (time) ------------>
BACKBONE   [ Find item ] [ Order ] [ Pay ] [ Receive ] [ Return ]   ← user activities

           search by     add to    pay by   track       request
           name          cart      card     shipment    return      ← walking skeleton
- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -  release 1
           filter by     save for  pay by   delivery    print
  ↓        category      later     invoice  SMS         label
less - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -  release 2
essential  search by     wish      pay in   choose      refund
           attributes    list      parts    slot        to card
```

Left-to-right is the **narrative** — the order a user experiences things, not priority. Down is priority and detail. Each release slice cuts across *all* activities so every release is usable end to end; the thinnest such slice is the walking skeleton.

For an analyst the map earns its keep by exposing **gaps** (an activity with no stories under it) and **imbalance** (one activity beautifully covered, the next unusable) — both invisible in a ranked list. Build the backbone with stakeholders in the room as the output of a workshop, then fill downward. The release plan falls out as a by-product. More on slicing mechanics in `prioritization.md`.

## The hierarchy: theme → epic → feature → story

| Level | Size | Typical form | Acceptance |
|---|---|---|---|
| Theme / initiative | Quarters | Business objective plus a metric | Business outcome measured |
| Epic | Weeks to months | A capability statement, often a hypothesis with a success metric | Defined by its child features |
| Feature | 1–3 sprints | "Credit-limit control on sales orders" | Feature-level criteria plus a demo |
| Story | ≤ 1 sprint, ideally 1–3 days | `As a … I want … so that …` | 3–7 acceptance criteria |
| Task | Hours | Imperative | Per the Definition of Done |
| Spike | Timeboxed | A question, a timebox, a required output | The question is answered in writing |

Mapped onto the requirement levels in `requirements-engineering.md`: theme ≈ business requirement, epic/feature ≈ stakeholder requirement, story plus criteria ≈ functional solution requirement. Non-functional requirements cut across all of them and belong in the Definition of Done or as their own explicitly constrained stories — never silently assumed.

## Definition of Ready / Definition of Done

**Ready** — entry criteria into a sprint. A gate, not bureaucracy; keep it to about ten items, or you have recreated a waterfall stage gate.

```
[ ] User-story form with a truthful "so that"
[ ] Acceptance criteria written, agreed with the owner, and testable
[ ] Small enough to fit comfortably in one sprint
[ ] INVEST-checked
[ ] Dependencies identified and resolved or scheduled earlier
[ ] External interfaces and data contracts specified, or a spike scheduled
[ ] Inputs available: mockups where a UI is involved, test data, environment
[ ] Relevant non-functional requirements stated, or explicitly deferred to the DoD
[ ] Estimated by the team
[ ] No open blocking questions (open questions have an owner and a date)
```

**Done** — exit criteria applied to every story. This is where cross-cutting requirements live so they don't have to be restated each time.

```
Code      [ ] Complete and follows the agreed standards (for 1C: Стандарты разработки 1С)
          [ ] Reviewed and merged, no open comments
Test      [ ] Every acceptance criterion demonstrably met
          [ ] Automated tests written and green
          [ ] Checked against the DoD non-functional list (performance budget,
              access rights, audit logging)
          [ ] Tested with realistic data volumes
Data      [ ] Roles and access rights configured and verified for every affected role
          [ ] Migration / upgrade path handled; no undocumented manual steps
Docs      [ ] User-facing help or release note updated
          [ ] Requirement ↔ object ↔ test links recorded
          [ ] Analyst artifacts updated: process model, data model, glossary
Deploy    [ ] Deployed to the demo environment and accepted by the owner
          [ ] No known defects of severity Major or above left open
```

Both are team agreements, visible, and revised at retrospectives. Never allow "done except…" — that phrase is how a release slips one story at a time.

## Acceptance criteria: rules vs scenarios

**Rule-oriented** — a numbered list of constraints:

```
1. The credit check runs on transition to "Confirmed", not on save as draft.
2. Overdue balance = the sum of unpaid receivables past their due date, in the
   contract currency, as of the current date.
3. If overdue balance + order total > credit limit, confirmation is blocked.
4. A blocked confirmation shows the limit, the overdue balance, the order total
   and the shortfall.
5. Users with the Credit Override role may confirm anyway; doing so writes an
   audit entry.
6. A credit limit of 0 means unlimited.
7. Orders in another currency are converted at the central bank rate on the
   order date.
```

Use this for business rules, field validation, permission matrices, rounding and posting rules, and anything non-functional — most ERP acceptance criteria, in other words. It is also what business readers actually read.

**Scenario-oriented** — Given/When/Then, for behaviour that is genuinely *state → event → outcome*:

```gherkin
Feature: Credit limit control on sales orders

  Rule: An order may not be confirmed if it pushes the customer over their limit

    Background:
      Given customer "Alpha LLC" has a credit limit of 10 000 GEL

    Example: An order within the available limit is confirmed
      Given "Alpha LLC" has an overdue balance of 2 000 GEL
      When a sales manager confirms an order for 5 000 GEL
      Then the order status is "Confirmed"

    Example: An order exceeding the limit is blocked
      Given "Alpha LLC" has an overdue balance of 8 000 GEL
      When a sales manager confirms an order for 5 000 GEL
      Then the order is not confirmed
      And the manager is told the order exceeds available credit by 3 000 GEL

    Example: A credit controller may override the block
      Given "Alpha LLC" has an overdue balance of 8 000 GEL
      When a credit controller confirms an order for 5 000 GEL
      Then the order status is "Confirmed"
      And an audit entry records the credit override
```

Use scenarios when the variations carry meaning, when you want the criteria to become automated tests, or when a concrete example settles an argument that prose can't. Don't force a static constraint ("the phone field accepts +995 followed by nine digits"), a field list, a layout rule or a performance budget into Given/When/Then — it produces unreadable ceremony.

**Most real stories want both**: a short rule list for the constraints, plus two to five key scenarios for the interesting behaviour. Not every combination — only the examples that carry meaning.

## Gherkin, and how it goes wrong

| Anti-pattern | Instead |
|---|---|
| UI-coupled steps: `Given I visit "/login"`, `When I enter "bob" in the field`… | `When Bob logs in` — the mechanics belong in the step definitions |
| Conjunction in one step: `Given I have shades and a Mustang` | Two steps; `And` exists for exactly this |
| Several rules in one scenario | One scenario, one behaviour; group with `Rule:` |
| `Then` steps that act: `Then I click Save and the record is stored` | `Then` only observes; actions belong in `When` |
| Two `When`s | Two scenarios, or setup that belongs in `Given` |
| A 30-step test script | Declarative, about seven steps. Thirty steps is a journey test, not a specification |
| Incidental detail: `Given a user with id 4711, created 2021-03-02, status A…` | Only the data that affects the outcome |
| Vague outcome: `Then it works` | Observable, specific, falsifiable |
| Five near-identical scenarios differing by one value | `Scenario Outline` with an `Examples` table |
| Twelve lines of `Background` | Four at most; more means the scenarios are over-coupled |
| First-person "I" everywhere | Name the role — `When the credit controller…` |
| Gherkin for a performance requirement | A fit criterion in the DoD, tested by a load tool |

Keywords available: `Feature` · `Rule` · `Example`/`Scenario` · `Given`/`When`/`Then`/`And`/`But` · `Background` · `Scenario Outline` with `Examples` and `<placeholders>` · doc strings · data tables · tags.

## Specification by example

The process, in order: derive scope from goals → specify collaboratively (the three amigos: analyst, developer, tester) → illustrate with examples → refine, stripping incidental detail down to the key examples → automate validation without changing the specification → validate frequently → let the specifications become living documentation.

The payoff worth naming to a sceptical team: documentation that cannot silently go stale, because when it does it fails the build.

## Acceptance criteria for ERP work

A few criteria types recur in 1C and ERP stories and are almost always missing on the first draft. Add them deliberately:

- **Posting and register effects.** Which registers move, with what sign, and in what quantity. "The document posts" is not a criterion; "posting writes a Расход movement to the Товары на складах register for each line, in the document's warehouse, on the document date" is.
- **Reversal and re-posting.** What happens on unposting, on re-posting after an edit, and on marking for deletion. This is where most defects live.
- **Period boundaries.** Behaviour when the accounting period is closed, at month end, and when the document date differs from the entry date.
- **Rights and visibility.** Which roles can see, create, post and unpost it — and, where row-level security applies, which rows each role sees. Express as a matrix, not prose.
- **Rounding and currency.** Rounding rule, precision, which rate on which date, and which amount is authoritative when they disagree.
- **Printed forms and reports.** Which layout, what appears when a field is empty, and behaviour on multi-page output.
- **Exchange and integration.** What is sent, when, what happens on failure, and whether re-sending the same document twice is safe.
- **Volume.** The realistic row count the criterion must hold at — a rule that works on 10 lines and not on 10,000 has not been accepted.

Each of these maps to something a developer must decide anyway. Deciding it in the acceptance criteria costs a sentence; deciding it during acceptance testing costs a sprint.
