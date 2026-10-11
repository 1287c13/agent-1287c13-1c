# SRS & ТЗ — Standard Document Structures

Read this when the deliverable has to satisfy a standard or a contract rather than only a team: an SRS, a ГОСТ ТЗ, a ЧТЗ for a 1C modification, or a tender annex. The choice of skeleton is not cosmetic — a customer whose procurement expects ГОСТ 34.602 will reject a beautifully written PRD, and a delivery team handed a 90-page ГОСТ document with no user flows will build the wrong thing anyway. Often you need both, at different moments.

## Contents
- Which document when
- ISO/IEC/IEEE 29148 — SRS
- ISO/IEC/IEEE 29148 — SyRS and StRS
- IEEE 830 (legacy, still common)
- Volere and the snow card
- ГОСТ 34.602-2020
- ГОСТ 19.201-78
- ТЗ vs PRD
- The pragmatic hybrid

## Which document when

| Situation | Document |
|---|---|
| Internal product team, iterative delivery | PRD / product brief — see `prd-writing.md` |
| Software product, formal but not contractual | SRS per 29148 |
| State, quasi-state or fixed-price contract in the CIS | ТЗ per ГОСТ 34.602-2020 |
| A single program or utility rather than a whole system | ТЗ per ГОСТ 19.201-78 |
| One gap inside a 1C implementation | ЧТЗ / постановка задачи — see `1c-erp-analysis.md` |
| Requirements to be reused and traced individually | Volere snow cards over any skeleton |

## ISO/IEC/IEEE 29148 — SRS

```
1. Introduction
   1.1 Purpose
   1.2 Scope
   1.3 Product overview
       1.3.1 Product perspective
       1.3.2 Product functions
       1.3.3 User characteristics
       1.3.4 Limitations
   1.4 Definitions
2. References
3. Specific requirements
   3.1 External interfaces
   3.2 Functions
   3.3 Usability requirements
   3.4 Performance requirements
   3.5 Logical database requirements
   3.6 Design constraints
   3.7 Software system attributes
   3.8 Supporting information
4. Verification              ← parallel in structure to clause 3
5. Appendices
   5.1 Assumptions and dependencies
   5.2 Acronyms and abbreviations
```

The one section worth caring about most is **clause 4, Verification**, structured to mirror clause 3: every requirement gets a verification method — inspection, analysis, demonstration or test — decided at authoring time, not at test time. That single constraint is what makes "verifiable" mean something, because a requirement you can't say how to verify gets rewritten while it's still cheap.

## ISO/IEC/IEEE 29148 — SyRS and StRS

The standard defines a ladder that mirrors the four levels of requirement: **BRS → StRS → SyRS → SRS**.

**SyRS** (system, not just software) adds sections an SRS omits and an ERP project usually needs: system modes and states, system operations, environmental conditions, information management, policies and regulations, life-cycle sustainment.

**StRS** is the business-facing one, and its outline is a good checklist for an обследование report: business environment · goals and objectives · business model · information environment · business processes · operational policies and rules · operational constraints · modes · quality · structure · user requirements · concept of the proposed system with operational scenarios · project constraints.

## IEEE 830 (legacy, still common)

Superseded by 29148 but still what many organizations mean when they say "SRS":

```
1. Introduction (purpose, scope, definitions, references, overview)
2. Overall description
   2.1 Product perspective (system/user/hardware/software/communications interfaces,
       memory constraints, operations, site adaptation)
   2.2 Product functions   2.3 User characteristics   2.4 Constraints
   2.5 Assumptions and dependencies   2.6 Apportioning of requirements
3. Specific requirements
   3.1 External interface requirements
   3.2 Functional requirements
   3.3 Performance requirements
   3.4 Design constraints
   3.5 Software system attributes (reliability, availability, security,
       maintainability, portability)
   3.6 Other requirements
4. Appendixes   5. Index
```

Clause 3 can be organized six ways (the annex gives eight templates, since "by mode" has two variants and one template shows several organizations combined) — by mode, user class, object, feature, stimulus, or functional hierarchy. For ERP and 1C work, **by feature** or **by user class** reads best for business readers, and **by object** aligns almost exactly with 1C metadata, which makes handoff to development cleaner. Pick one and say which in clause 1.

## Volere and the snow card

Volere's 27-section template is more than most projects need, but three ideas are worth stealing whatever skeleton you use.

**The snow card** — the atomic requirement shell:

```
Requirement #:            Type:                 Event / use case #:
Description:              one sentence of intent
Rationale:                why this is needed
Originator:               who raised it
Fit criterion:            the quantified measure proving it is met
Satisfaction: 1–5         Dissatisfaction: 1–5
Priority:                 Conflicts:
Supporting materials:     History:
```

**Fit criterion** is the best idea in the template: it separates the quantification from the requirement text, so the requirement stays readable while remaining testable. It is the cleanest way to tame non-functional requirements, and it makes the "verifiable" characteristic operational rather than aspirational.

**The waiting room** — a formal parking lot for out-of-scope requirements. It prevents both scope creep and the loss of good ideas, and it gives you something concrete to point at when you say "not this release".

**Work partitioning by business event** rather than by org unit. Org charts change; business events ("a customer places an order", "a month ends") don't, so scope defined by events is far more stable.

## The rest of the ГОСТ 34 family

ГОСТ 34.602 does not stand alone, and an acceptance committee will ask about the others:

| Standard | What it governs | When you need it |
|---|---|---|
| **ГОСТ 34.601-90** | Стадии и этапы создания АС — where предварительные испытания, ОЭ and приёмочные испытания are actually defined | Writing §5 Состав и содержание работ and §7 Порядок контроля и приёмки |
| **РД 50-34.698-90** | Required content of AS documents — Руководство пользователя, Пояснительная записка, ПМИ and the rest | Filling §9 Требования к документированию, which is normally written as a reference to it |
| **ГОСТ 34.603-92** (and ГОСТ Р 59795-2021) | Виды испытаний АС | Designing the acceptance programme — see `1c-erp-analysis.md` |
| **ГОСТ 34.003** | Terms and definitions | When the glossary section is disputed |

## ГОСТ 34.602-2020

In force since 1 January 2022, replacing ГОСТ 34.602-89. The reference structure for state, quasi-state and large corporate 1C/ERP contracts in the CIS. **Ten sections, and none of them may be omitted** — if nothing is required in a section, it stays with the note «Требования не предъявляются».

```
1  Общие сведения
2  Цели и назначение создания (развития) АС
3  Характеристика объектов автоматизации
4  Требования к АС
5  Состав и содержание работ по созданию АС
6  Порядок разработки АС                    ← new in 2020
7  Порядок контроля и приемки АС
8  Требования к составу и содержанию работ по подготовке объекта
   автоматизации к вводу АС в действие
9  Требования к документированию
10 Источники разработки
```

**§1 Общие сведения** — full name and code of the system; customer and contractor with details; the documents the work is based on; planned start and end dates; funding source and order; how results are presented and accepted.

**§2** — goals **with measurable target values**, and purpose (which activities are automated, which objects).

**§4 Требования к АС** is the bulk of the document:

```
4.6.1 Требования к структуре АС в целом
      subsystems, interfaces with adjacent systems, operating modes,
      diagnostics, planned development
4.6.2 Требования к функциям (задачам)
      per subsystem: list of functions, timing rules, quality of
      implementation, output form, accuracy and reliability of results
4.6.3 Требования к видам обеспечения
      математическое · информационное · лингвистическое · программное ·
      техническое · метрологическое · организационное · методическое
4.6.4 Общие технические требования к АС     ← all NFRs gathered here in 2020
      personnel numbers and qualification · показатели назначения ·
      надёжность · безопасность · эргономика · транспортабельность ·
      эксплуатация и обслуживание · защита от НСД · сохранность
      информации при авариях · защита от внешних воздействий ·
      патентная чистота · стандартизация и унификация · дополнительные
```

**What changed in the 2020 edition**, worth knowing when someone hands you an old template: a new section «Порядок разработки АС» (stages, steps, performers); all non-functional requirements consolidated into «Общие технические требования»; explicit **quality criteria for requirements** — единичность, непротиворечивость, актуальность, выполнимость, проверяемость, однозначность, which echo 29148 almost item for item; and the rule that changing the ТЗ follows the same approval route as the original, which is what makes it a contractual instrument rather than a document.

The 89 edition, still encountered, had nine sections: общие сведения · назначение и цели · характеристики объекта автоматизации · требования к системе · состав и содержание работ · порядок контроля и приёмки · подготовка объекта к вводу · требования к документированию · источники разработки.

## ГОСТ 19.201-78

For a *program* rather than a whole automated system — much lighter, and the right choice for a single 1C data processor, report or integration component.

```
1. Введение
2. Основания для разработки
3. Назначение разработки
4. Требования к программе или программному изделию
   4.1 требования к функциональным характеристикам
   4.2 требования к надёжности
   4.3 условия эксплуатации
   4.4 требования к составу и параметрам технических средств
   4.5 требования к информационной и программной совместимости
   4.6 требования к маркировке и упаковке
   4.7 требования к транспортированию и хранению
   4.8 специальные требования
5. Требования к программной документации
6. Технико-экономические показатели
7. Стадии и этапы разработки
8. Порядок контроля и приёмки
```

Sections may be merged, added to or refined depending on the program.

## ТЗ vs PRD

They are different genres serving different purposes, and treating one as a sloppy version of the other is the source of a lot of wasted effort.

| | ТЗ (ГОСТ) | PRD |
|---|---|---|
| Legal status | Contract annex; the basis for acceptance and payment | Internal working document |
| Purpose | Define the contractor's obligation and the acceptance criteria | Align a team on what to build and why |
| Audience | Procurement, legal, acceptance committee, auditors | PM, design, engineering, QA |
| Author | Customer, often with the contractor; signed by both | Product manager |
| Bias | *What must be delivered* — work composition, stages, documentation, acceptance order | *Why* — problem, users, success metrics, non-goals, open questions |
| Structure | Fixed by the standard; sections can't be omitted | Free-form |
| Change | Formal — the same approval route as the original, usually a contract amendment and re-pricing | Edit the document, tell the team |
| Non-functional | Mandatory, explicit sections | Often thin |
| Verification | Порядок контроля и приёмки: предварительные испытания, опытная эксплуатация, приёмочные испытания | Acceptance criteria per story |

On a real 1C/ERP project you typically need several, at different moments: a **концепция / бизнес-требования** or PRD-style document at the start to agree why and what value; **ФТ (функциональные требования)** per subsystem as the working analyst artifact; a **ТЗ по ГОСТ 34.602** as the contractual umbrella when the customer is state-linked or the contract is fixed-price; and a **ЧТЗ на доработку** per gap, referencing the fit-gap register.

## The pragmatic hybrid

The approach that passes a ГОСТ review while still being usable by a delivery team: **keep the ГОСТ 34.602 section skeleton**, and inside §4.6.2 «Требования к функциям (задачам)» place structured requirements written in EARS form or as user stories with acceptance criteria — each with an ID, a priority and a fit criterion. The standard prescribes the section structure, not the *form* of the requirements inside a section, so this is compliant and far more testable than the prose those sections usually contain.

Two practical notes for Georgian-language work. When the contract language is Georgian, keep the ГОСТ section numbering and titles in their canonical Russian form in parentheses after the Georgian heading — acceptance committees and auditors look for the numbering, and a translated-only heading makes the document hard to review against the standard. And keep a **glossary section** in every document, Georgian term first with the Russian and English equivalents alongside, because a large share of what looks like requirement conflict turns out to be two departments using one word for two things.
