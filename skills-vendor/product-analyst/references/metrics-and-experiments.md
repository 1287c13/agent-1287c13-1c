# Metrics, OKRs & Experiments

Read this when the question is "how will we know this worked?" — choosing a metric, writing OKRs, setting guardrails, or deciding whether an experiment is even the right instrument. A requirement with no way to observe its effect is a requirement nobody can tell you to stop maintaining.

## Contents
- North Star and input metrics
- Leading vs lagging
- HEART (goals → signals → metrics)
- AARRR, and why it's a loop
- Guardrails and counter-metrics
- Writing OKRs that aren't task lists
- A/B tests: sizing, duration, and when not to
- Metrics in an ERP context

## North Star and input metrics

A North Star metric is a single rate, count or ratio that connects the customer problems you're solving to sustainable business results. Three qualities: it expresses **customer value**, it sits within the team's **sphere of influence**, and it is a **leading** indicator.

Seven tests for a candidate: does it express customer value (not DAU, not registrations)? Could a stranger infer your strategy from it? Does it predict medium-term growth? Can teams actually influence it? Can you explain it to a non-technical colleague? Can you instrument it at reasonable cost? And — the vanity test — **would it go up if all product development stopped?** If yes with no explanation, it's vanity. Registered users, page views, downloads, impressions and time-on-page all fail this.

**Input metrics** are where the work actually happens. The North Star is the dependent variable; inputs are the independent ones. The counterintuitive rule: *if you can move your North Star directly, it probably isn't a good North Star* — it should stay one level out of reach so teams have to reason about causes.

Good inputs are **influential** (they move the North Star), **complementary** (together they produce it), **actionable** (daily work touches them), **independent** (moving one doesn't automatically move another) and **few** — three to six.

```
        business results + customer value
                     ↑
             NORTH STAR METRIC
                     ↑
   [input 1]  [input 2]  [input 3]  [input 4]
                     ↑
                  THE WORK
```

A useful diagnostic: list the current initiatives and check that each connects to an input. Gaps mean either the inputs are incomplete or the work is misdirected.

Three product archetypes usually settle the first argument in a metric workshop: the **attention game** (time correlates with satisfaction — social, streaming), the **transaction game** (value is ease and reliability — commerce, delivery), and the **productivity game** (value is task completion and efficiency — tools, and almost all ERP work).

Change the North Star when the metric flattens while revenue moves, when strategy shifts materially, when the market changes, or when it proves uncontrollable despite real effort. Teams get attached to their metric, and that attachment is itself the risk.

## Leading vs lagging

| | Leading / input | Lagging / output |
|---|---|---|
| Tells you | What will happen | What happened |
| Examples | Activation rate, session frequency, engagement depth, error rate | Revenue, churn, LTV, margin |
| Actionability | High — correct course this week | Low — moves over months |
| Right use | Team objectives, weekly review, experiments | Company goals, board reporting |

To find a leading indicator for a lagging goal: define the lagging goal → identify behaviours that *precede* success → test the correlation → if it doesn't hold, pick different candidates → keep validating, because the correlation decays.

The rule: give a product team a leading metric they can move; hold the company to the lagging one. Handing a lagging business metric to a single team is how you get a demoralized team and a meaningless target.

## HEART (goals → signals → metrics)

Five dimensions, and you deliberately **do not use all five** — pick the ones that match the goal and leave the other rows blank.

| Dimension | What it captures | Example metric |
|---|---|---|
| Happiness | Attitude, satisfaction (subjective) | CSAT, CES, survey rating |
| Engagement | Frequency and depth of interaction | Sessions per user per week, documents created |
| Adoption | New users, or uptake of a new capability | Trial→paid conversion, % of existing users using the new feature in 30 days |
| Retention | Keeping users over time | Cohort retention % |
| Task success | Efficiency, effectiveness, error rate | Completion rate, time on task, error rate |

The actual framework is the **goals → signals → metrics** process; HEART is just the taxonomy. For each relevant dimension: what does success *mean* here (not how you'd measure it)? → what observable behaviour or attitude would indicate success or failure? → what specific number tracks that signal? Have the team write the goals separately and then reconcile — the disagreement is the most valuable output of the exercise.

Two mechanical rules. **Use ratios, not raw counts**: 120 of 200 returning users is 60% retention and comparable across cohorts; "120 users" rises with growth and can hide a deteriorating experience. And **start narrow** — add dimensions later.

## AARRR, and why it's a loop

Acquisition (how they arrive) → Activation (reaching the moment value is understood) → Retention (coming back) → Referral (becoming advocates) → Revenue (paying, profitably).

The framework's main weakness is the linear reading. Acquiring users into a leaky product wastes money, so in practice invert it — **retention and activation first**, and treat referral as feeding back into acquisition rather than as a terminal stage. Roughly 80% of effort on optimizing what exists, 20% on new.

## Guardrails and counter-metrics

A guardrail is a secondary metric watched alongside the primary one to catch damage elsewhere — because a change can look like a win and quietly break something adjacent. The hierarchy: North Star (strategy) → primary metric (this change's success) → guardrails (unintended impact).

| Category | What it catches | Example pairing |
|---|---|---|
| Cannibalization | Gains stolen from another surface | New surface engagement ↑ → main flow engagement |
| Product health / trust | Quality degrading while volume rises | Bookings ↑ → ratings, refund rate |
| Technical | Friction introduced regardless of merit | Any change → p95 latency, error rate |

Mechanics that make guardrails work: pick **two or three**, not ten (more guardrails means more false alarms and a change blocked for noise); set the **threshold and the action before launch** ("we ship unless p95 latency degrades by more than 100 ms or refund rate rises more than 0.5 pp"); treat a breach as an **escalation review**, not an automatic kill; and keep a small standing set (latency, error rate, support contact rate) on everything.

In OKRs, a guardrail is what lets you set an aggressive target safely: "increase X by 20% **without** Y falling below Z."

## Writing OKRs that aren't task lists

Three distinct things, and conflating the last two is what breaks most OKR sets:

| Element | Answers | Property |
|---|---|---|
| Objective | Where do we want to go? | Qualitative, directional |
| Key result | How do we know we're getting there? | A quantitative **outcome** you influence but can't guarantee |
| Initiative | What will we do about it? | A task or project you fully control |

**Three tests for "is this key result actually an initiative?"**
1. **Control test** — could you guarantee it purely by working hard? Then it's an initiative.
2. **Binary test** — is it answerable yes/no ("shipped: yes")? Then it's an initiative.
3. **Verb test** — does it start with *launch, build, ship, deliver, implement, migrate, complete, roll out, hire*? Then it's an initiative.

A real key result starts with *increase / reduce / grow / improve / maintain* and carries a number, a baseline and a date.

| Output disguised as a key result | Outcome key result |
|---|---|
| Launch the new onboarding flow | Increase 7-day activation from 34% → 42% |
| Complete the migration | Reduce p95 API latency from 800 ms → 300 ms |
| Run 10 customer interviews | Increase the share of teams doing weekly discovery from 20% → 60% |
| Send out a press release | Get covered in 20 media outlets |

One honest caveat: on infrastructural or heavily ambiguous work an outcome key result may genuinely be unmeasurable inside the quarter, and some frameworks deliberately allow a *commitment* to be a deliverable. That's fine — be explicit that you are committing to a deliverable, rather than dressing a deliverable up as an outcome.

Other common failures: **cascading** objectives down through managers into individual goals, which fragments a cross-functional team into people pulling in different directions — use team objectives; **too many** (one objective, at most two, with two to four key results per team per quarter); **sandbagging**, which is what you get when OKRs are tied to compensation; **no baseline** ("increase activation to 40%" is meaningless without "from 34%"); and **no guardrail**, which invites gaming.

## A/B tests: sizing, duration, and when not to

**Four inputs to any sample size:** baseline rate · minimum detectable effect (set from what would change your decision, not from what you hope for) · significance level, conventionally α = 0.05 · power, conventionally 0.80.

Useful approximations: for proportions, per-variant `n ≈ 16 × p(1−p) / δ²`; for continuous metrics, `n ≈ 16 × σ² / δ²`. The δ² is the whole story — **halving the MDE quadruples the sample you need**. Most "we don't have enough traffic" problems are really "our MDE is unrealistically small."

**Duration:** at least one full business cycle, preferably two — so one to two weeks minimum, since weekdays and weekends differ. Practical range two to four weeks; past four to six weeks, cookie churn and outside events contaminate the result. Fix the duration from the sample-size calculation up front; "run until it's significant" is not a duration, and stopping at the first significant reading inflates your false-positive rate far above 5% because you are effectively running many tests.

**When not to A/B test** — ask first: will the result change what we do? can the design identify the effect? do we have the power? is exposing users acceptable? is this the *cheapest* way to find out? can we keep the treatment clean?

| Situation | Do this instead |
|---|---|
| Insufficient traffic | Qualitative research, bigger swings, or ship on judgement and monitor |
| Compliance or mandatory fix | Staged rollout with guardrails — don't withhold a required fix to prove it helps |
| Catastrophic or irreversible downside | Expert review, simulation, tightly controlled pilot |
| Marketplaces / networks (users interfere with each other) | Switchback or cluster randomization |
| Obvious bug fix | Tests plus controlled rollout |
| Big strategic redesign you'd ship anyway | Ship it; test the components |
| Change too small to matter | Pick one and monitor |
| No clear hypothesis | Write the hypothesis first, or don't run it |
| Using the test to avoid making a decision | Fix the alignment problem in conversation |

Pair quantitative with qualitative: behaviour data tells you *what* changed, research tells you *why*. Don't build a causal story after the fact out of secondary metrics. The governing principle is measurement proportional to uncertainty, risk and reversibility — not "test everything."

## Metrics in an ERP context

Most internal ERP and 1C work cannot be A/B tested at all: there is one organization, everyone cuts over at once, and the population is a few hundred users. That doesn't excuse skipping measurement — it changes the instrument. What works instead:

- **Before/after on a process metric with a defined measurement window**: time to close the month, documents posted per operator per day, share of documents needing manual correction, days sales outstanding, stock discrepancy at inventory count.
- **A baseline captured before cutover.** This is the step teams skip and then regret, because after go-live nobody can prove anything improved. Capture the baseline during обследование, while you are already collecting volumes.
- **Parallel running** as the nearest thing to a control: the old and new process run on the same period, and the reconciliation difference is your measurement.
- **Guardrails still apply**: posting errors, closing time, support tickets per week, and the number of workarounds people invent — a spreadsheet appearing next to the system is the clearest signal that a requirement was wrong.
- **Adoption as a leading indicator**: share of transactions entered in the system rather than retrofitted, share of users active weekly, share of documents entered on the day of the event rather than in a batch at month end.

State the measurement plan in the document even when it's manual, and name who pulls the number and when. An unowned metric isn't measured.
