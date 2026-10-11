# Discovery & Research

Read this when the user is still deciding **what** to build, or when a request arrives as a solution with no stated problem behind it. Discovery's whole job is to keep the team from confidently shipping the wrong thing. All prose output stays in Georgian; the frameworks and their canonical names stay in their original form.

## Contents
- Outcome vs output — the distinction everything hangs on
- Opportunity Solution Tree
- Customer interviews: story-based technique
- Jobs-to-be-Done and the Four Forces
- The four risks and assumption mapping
- Evidence types and prototype flavors
- Problem validation vs solution validation
- Discovery output template

## Outcome vs output

The single most common failure in a product request is that it names an **output** ("build a mobile app", "add an approval workflow") and never states the **outcome** it is supposed to produce. Your first job is to convert one into the other.

| Level | What it is | Character |
|---|---|---|
| Output | Something you ship: a feature, a project | Binary — did we ship it? |
| Business outcome | Revenue, margin, retention, market share | Lagging; rarely inside one team's control |
| Product outcome | A measurable change in customer behaviour | Leading; inside the team's control |
| Traction metric | Adoption of one specific feature | Too narrow to steer by |

Josh Seiden's definition is the one to hold: *an outcome is a change in human behaviour that drives business results.*

**The conversion, in four moves:** state the output → ask "what's the value / how would we know this worked?" → surface the hidden outcome → scope it so it is measurable. "Build an Android app" → "engage more users" → "increase engaged mobile users".

**Checklist for a stated outcome** (Torres's failure list, compressed). Flag it if the outcome is:
1. An output wearing an outcome's clothes (answerable yes/no).
2. Not connected to any business value — then nobody will fund it.
3. Outside the team's span of control ("grow company revenue" handed to one squad).
4. A single feature's adoption. Her test: *could a happy customer never use this feature?* If yes, its adoption is not your outcome.
5. So dependent on other teams that the team can't move it alone.
6. Measuring the action instead of the value of the action — a job board measuring "applications submitted" misses "got hired". On day one it doesn't have to be measurable, only directional.
7. Sentiment only (NPS/CSAT). Find the behaviours satisfied customers exhibit and measure those.
8. Wired straight into performance reviews — that buys you sandbagging, not learning.

## Opportunity Solution Tree (Teresa Torres)

Four layers, root at the top:

1. **Outcome** — one product outcome.
2. **Opportunity space** — customer needs, pain points and desires that, if addressed, move that outcome.
3. **Solution space** — solutions explored for **one** selected opportunity.
4. **Assumption tests** — how you decide which solution actually creates value.

**The opportunity test:** *is there more than one way to address this?* If only one response exists, it is a solution in disguise. "I want to eat out" is a solution; "I don't have time to cook" and "I want something better than I can make" are opportunities.

**Where opportunities come from:** story-based interviews. Generating them from your own head imports your biases. Support tickets, sales calls and analytics can *inspire* what to ask about, but they lack the context you need to map from.

**The nine-step sequence:** verify prerequisites (a target-customer theory, a defined outcome, 3–4 interviews already done) → put the outcome at the top → map the opportunity space → select **one** target opportunity → brainstorm solutions for that opportunity only → pick **three** to explore → surface assumptions and prioritize tests → test the riskiest assumption from each of the three → evaluate and iterate.

**Prioritizing opportunities** on four subjective factors — opportunity sizing (how many, how often), market factors, company/strategy fit, and importance to the customer. Compare **siblings only**: settle the top row first, then drop into the winner's branch and ignore the rest. Torres deliberately refuses a scoring formula here, and she is right — these are judgement calls and a number would launder them into false fact. Also: do not kill an opportunity because it *looks* expensive. Effort is a property of solutions, and you have not chosen one yet.

**Cadence:** revisit the space every 3–4 interviews; the top-level moments usually stabilize after 6–8.

## Customer interviews: story-based technique

Interview weekly as a habit, not as a project. Separate the **research question** (what you want to learn) from the **interview question** (what you actually say), because people are bad at answering direct questions out of context.

**Ask — past behaviour, one specific instance:**
- "Tell me about the **last time** you [did the activity]."
- "…the last time you did it **in [context]**." (narrows scope)
- "Walk me through that — what happened next?"
- "Who else was involved?" / "What were you doing right before that?"
- "You said it was frustrating — tell me about a specific time that happened."

**Don't ask — speculative, generalized, leading:**
- "Would you use this?" / "Would you pay for this?" — predicts nothing.
- "How often do you usually…?" — invites an estimate instead of a story.
- "What features do you want?" — asks the customer to do your job.
- "Do you find X frustrating?" — you just supplied the answer.
- "What would make this better?"

**The golden rule:** let the participant talk about what they care about most. If they won't give you the story you were fishing for, take the value that is actually there.

**Interview snapshot** — one per interview, written in 15–20 minutes while it's fresh: name, photo, quick facts (role, org, product familiarity — this is what lets you segment opportunities later), a memorable quote, opportunities, insights not yet opportunities, and a small experience map of that person's story.

## Jobs-to-be-Done: the Four Forces of Progress

**Push + Pull > Anxiety + Habit** is when someone switches.

| Force | Direction | What it is |
|---|---|---|
| Push of the situation | toward change | What is broken about today — locate this first |
| Pull of the new solution | toward change | The better life they imagine — not a feature list |
| Anxiety of the new solution | away | "What if it doesn't work? What about my data?" — the most overlooked force |
| Habit of the present | away | Inertia, switching cost, familiarity |

The strategic point: you must both raise the motivating forces and lower the restraining ones. Teams overwhelmingly work on Pull and ignore Anxiety and Habit — which is what actually blocks most decisions. In an ERP rollout, anxiety and habit are usually the *dominant* forces, and no amount of extra functionality touches them; training, parallel running and a reversible cutover do.

**Switch interview:** rebuild the timeline backwards from the switch — first thought → passive looking → active looking → deciding → buying → using. Anchor on concrete events ("What day was it? Who else was in the room?") so you get memory rather than rationalization.

**Job story format:** `When [situation], I want to [motivation], so I can [expected outcome].` It drops the persona on purpose — demographics don't explain causality. Use it when the trigger and context matter more than the role; use the classic user story when the role genuinely changes the behaviour (which in ERP work it often does).

## The four risks and assumption mapping

Every solution carries four risks (Cagan), plus a fifth worth adding:

| Risk | The question | Usually owned by |
|---|---|---|
| Value | Will customers buy it / choose to use it? | Product manager |
| Usability | Can users figure out how to use it? | Designer |
| Feasibility | Can we build it with the time, skills and technology we have? | Lead engineer |
| Business viability | Does it work for the rest of the business — legal, finance, support, sales, brand? | Product manager |
| Ethical | Could building this cause harm? | The team |

Value is the hardest; business viability is the most often skipped.

**Assumption mapping (David Bland):** write each belief as "We believe that…", then place it on a 2×2 — **importance** (would the idea fail if this were wrong?) against **evidence** (do we have observable support?). The top-right quadrant — important, no evidence — is your riskiest assumption set, and it is the *only* quadrant that sets your near-term test queue.

To generate assumptions, walk the customer's journey step by step and name what must be true at each step; also walk the logic of your opportunity tree, audit the data you already have, and run a pre-mortem.

**Define success before running the test.** Decide what result would count as passing and write it down first; otherwise you will rationalize whatever you get.

## Evidence types and prototype flavors

| Prototype | Answers | Must not be used for |
|---|---|---|
| Feasibility prototype (minimal code) | Feasibility | UX or demand |
| Low-fi user prototype (wireframe) | Flow, information architecture | Visual design, realistic data |
| High-fi user prototype (static data) | **Usability** | Proving value — "I love it" predicts nothing |
| Live-data prototype (real data, limited traffic) | **Value**, quantitatively | Shipping as-is |
| Wizard-of-Oz / concierge (a human does what software will) | Value + feasibility of the service | Scale |

The pairing rule: usability risk → high-fi prototype plus a usability test; value risk → a demand test (fake door, landing page) or a live-data prototype. Never claim value validation from a high-fi prototype.

For qualitative value evidence, ask for a **costly signal** — a non-binding letter of intent, a shared calendar slot, access to the spreadsheet they use today — rather than a yes/no.

## Problem validation vs solution validation

| | Problem validation | Solution validation |
|---|---|---|
| Question | Is there a problem, whose, worth solving? | Does *this* solve it, can they use it, will they choose it? |
| Timing | Before committing to a direction | After a concept exists, before production build |
| Methods | Story-based interviews, contextual inquiry, journey mapping, ticket/log analysis | Usability tests, prototype tests, fake-door tests, concierge, A/B |
| Failure mode | Skipping it and validating a solution to a problem nobody has | Treating "they said they liked it" as validation |

## Discovery output template

Structure the Georgian deliverable like this. Keep it to one page unless the user asks for more — a discovery brief that nobody reads has failed.

```
## პრობლემა და კონტექსტი        — whose problem, in what situation, evidence
## სასურველი შედეგი (outcome)    — the product outcome + how it connects to business value
## შესაძლებლობები (opportunities) — clustered, sourced from interviews, siblings comparable
## ჰიპოთეზები და დაშვებები        — "ვვარაუდობთ, რომ…", marked by risk type
## რისკიანი დაშვებები            — the important + no-evidence quadrant only
## შემოწმების გეგმა              — test, audience, success criterion defined in advance
## ღია კითხვები                  — what we do not know and who can answer it
```

Never invent the evidence. If you have no interviews, no analytics and no tickets, say so in that section and mark every opportunity `[დასაზუსტებელია]` — an unsourced opportunity list is a brainstorm, and calling it research is how teams end up confidently wrong.
