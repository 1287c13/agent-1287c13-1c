# 1C / ERP Implementation Analysis

Read this whenever the work sits on a 1C:Enterprise or ERP implementation — обследование, fit-gap, постановка задачи для разработчика, приёмка, migration planning, estimation. This is where the generic analyst craft meets the specific economics of a vendor configuration, and the specific economics are what make or break the project budget three years later.

## Contents
- Where the analyst sits
- 1C implementation methodologies
- The de-facto artifact map
- Обследование: types, process, what to collect
- The interview question bank
- Описание AS-IS for a 1C project
- Fit-gap and the decision hierarchy
- Support modes and what they cost
- Extensions: what an analyst must know
- The gap register
- Постановка задачи разработчику
- Приёмка: ПМИ, test scenarios, контрольный пример
- Estimation
- Data migration and master data
- The risk register
- Sources for the figures in this file
- Handing off to the 1c-developer skill

## Where the analyst sits

The analyst's product is a decision, recorded so that other people can act on it: *what business problem are we solving, does the standard configuration already solve it, and if not, at what level do we intervene and what does that cost forever after.* The developer decides how the code looks; the analyst decides whether the code should exist at all, and that decision is worth far more money.

Two rules of thumb worth carrying into every conversation with a sponsor — and quote them **as practitioner rules of thumb with their source**, never as measured statistics, because this skill's own cardinal rule forbids presenting an unsourced figure as fact. Projects where customization stays **under about 20% of scope** are reported to succeed markedly more often. And pre-project analysis typically gets 8–10% of project time where practitioners argue 15–20% is warranted — most failures are programmed long before the first line of code. Sources for the figures in this file are listed at the end.

## 1C implementation methodologies

| Technology | Scope | Character |
|---|---|---|
| **ТСВ** — Технология стандартного внедрения | Small and mid-market, projects up to ~3 months | Light, minimal customization, heavy customer participation |
| **ТБР** — Технология быстрого результата | Any scale, usually SMB→mid | Agile-like: monthly results, monthly sign-off and payment, minimal interim documents |
| **ТКВ** — Технология корпоративного внедрения | Large projects, holdings, state corporations | Spiral with waterfall elements; built on PMBOK and ISO 9000 |
| **ТКЛ** — ТКВ Лайт | Medium and large | Formal management at minimal formalization cost |
| **ТКС** — Технология корпоративного сопровождения | After go-live | Support with SLA |

ТКВ is described two ways in 1C's own material and they are not the same list — don't mix them. The **formal life cycle has six phases**: инициация → концептуальное проектирование → архитектура системы → рабочий проект → опытная эксплуатация → ввод в промышленную эксплуатацию. The **spiral («по волнам») representation**, which is the one that maps to deliverables, runs seven stages with the middle ones repeating per wave:

| Phase | Key documents |
|---|---|
| Инициация | Устав проекта, список участников, регламент проектного офиса |
| Формирование требований | Протокол обследования, Отчёт об обследовании, ФТТ (функционально-технические требования) |
| Проектирование | Концептуальный проект; концепции ролевой модели, НСИ, миграции, интеграции, обучения |
| Разработка | Спецификации, сценарии тестирования, протоколы демонстрации |
| Подготовка к ОЭ/ОПЭ | План перехода и обеспечения непрерывности бизнеса, протокол миграции |
| Подготовка к ПЭ | Протокол приёмочных испытаний, актуализированная документация |
| Завершение | Анкета удовлетворённости, отзыв заказчика |

**ОЭ / ОПЭ / ПЭ — a distinction specific to 1C projects, and one whose definitions genuinely differ between methodologies. Pin the definition in the project charter before anyone budgets against it.**

- **ОЭ (опытная эксплуатация)** — the system is exercised on real processes in full scope, in conditions close to production, on a test period with data entered retrospectively. The strongest variant is replaying a *closed period whose reporting is already signed*, because then the reference answer exists and the exercise is a real test rather than a rehearsal.
- **ОПЭ (опытно-промышленная эксплуатация)** — trial *industrial* operation. In most methodologies the new system is already primary here: its output is used for real reporting and management while the team still fixes defects and the old system is kept read-only. Some project charters instead define ОПЭ as a period of **parallel entry into both systems** — a far more expensive reading, so never assume it.
- **ПЭ (промышленная эксплуатация)** — live, handed over to support.

A project may run only ОЭ, only ОПЭ, or ОЭ then ОПЭ. **Parallel entry is a cutover pattern, not a phase** (see `roadmap-and-planning.md`): it means every operation is keyed twice, so if a charter defines ОПЭ that way, timebox it explicitly, price the double entry, and say what ends it.

**ТКВ's fifth axiom is worth quoting to a sponsor:** IT projects have an *inverted* risk profile — risk rises as the project proceeds rather than falling, because the product is intangible and the uncertainty is in the requirements. This is the argument for spending more on analysis up front, and it lands better than an appeal to best practice.

Where ТКВ is weak, and you should compensate deliberately: requirements-gathering method, migration strategy (it has no notion of test waves), cutover detail, and the timing of acceptance testing — its ПСИ protocol tends to summarize earlier results rather than being an independent user acceptance test.

**Choosing between ТБР and ТКЛ in practice:** ТБР when the project splits into independent modules that each deliver value monthly, requirements will firm up as you go, and the relationship is trusting. ТКЛ when the system is logically indivisible, the customer wants one simultaneous launch, and management requires a budget and a ТЗ up front. A common hybrid: manage by ТКЛ, deliver in waves by ТБР.

For comparison, SAP Activate runs Prepare → Explore → Realize → Deploy → Run with a fit-to-standard workshop in Explore; the fit-gap logic below is the same idea.

## The de-facto artifact map

More practical than any single methodology — this is what projects actually produce:

| Stage | Artifacts |
|---|---|
| **Presale / diagnostics** | Опросный лист · План обследования · Протоколы встреч · Схемы процессов AS-IS · Концептуальная архитектура (the survey report with a solution vision) |
| **Design / modelling** | Схемы процессов TO-BE · Сценарий моделирования (step-by-step actions in a demo base) · Протоколы демонстрации · **Реестр функциональных требований** · **FIT/GAP оценка** · Концепция интеграции · Концепция миграции · **Проектное решение (ПР)** |
| **Development** | **ЧТЗ** per accounting block · **ЗНР** (development tasks) · Инструкции · Протоколы демонстрации · Листы согласования |
| **Preparing for ОПЭ** | **ПМИ** · Пользовательские инструкции by role · Сценарии приёмочного тестирования · План обучения · Протоколы обучения |
| **During ОПЭ** | **Рабочий журнал ОПЭ** · Акт устранения замечаний · **Протокол приёмочных испытаний** · План-график устранения некритичных замечаний |
| **Handover to ПЭ** | Руководство пользователя with glossary, templates and common errors |

Two structures worth memorizing: the **реестр функциональных требований** is `ID · описание · приоритет · автор · статус`, and the **проектное решение** covers goals · glossary · TO-BE processes · object layouts · attribute descriptions · performance · security.

## Обследование: types, process, what to collect

| Type | Duration | What it produces | Estimate accuracy |
|---|---|---|---|
| **Экспресс-обследование** | 2–4 weeks | Goals, functional perimeter by standard subsystem, risks, hardware requirements, high-level integrations. Output: a ТЗ for tender, a roadmap, a budget | ±10–20% |
| **Полное предпроектное обследование** | 1–3 months | All current processes, functional requirements at process-step level, master-data normalization plan, integrations at object level | ±15% |
| **Функциональное моделирование** | 3–6 months | A functional model, target processes expressed as actions *in the actual system*, costing methodology, migration order | ±5% — scope is fixed against a working prototype |

A useful benchmark: a 200–300 person company needs roughly 200–220 specialist hours of survey work.

**The process is three steps.** Collect (interviews with key users, heads of department and top management; study regulations and data structures; record everything in протоколы; ask for a copy of the information base or screenshots). Analyse (structure it, map AS-IS, design TO-BE, identify gaps). Document and agree (the block owner signs the протокол, noting their block's specifics and their wishes for the new system). That signature matters: it is what converts "somebody said" into an agreed fact.

**What to ask the customer for:**

*Organization and rules* — org structure (legal entities, branches, departments) and headcount · list of legal entities and their tax regimes · **учётная политика** for accounting, tax and management accounting, plus the chart of accounts · the period-close regulation · internal regulations and process descriptions · job descriptions · the approval authority matrix.

*Documents and forms* — **primary document forms and printed forms** as actual files, not descriptions · management reporting forms as real files · regulated reporting where there is specificity · contract templates.

*Master data* — exports of the catalogs: номенклатура, виды номенклатуры, характеристики, серии, единицы измерения, номенклатурные группы; контрагенты, партнёры, договоры, соглашения; склады, подразделения, кассы, ККМ; статьи затрат/доходов/ДДС, ЦФО, направления деятельности; физлица, контактные лица · current classifiers and coding rules · an assessment of duplicates and of how completely mandatory fields are filled.

*IT landscape and volumes* — systems in use and **which system is master for which data** · integrations with direction, format, transport, frequency and current problems · **versions and releases of external and regulatory services**, recorded in the project documentation — for a Georgian client that means the RS.ge endpoints (waybills, e-invoices, VAT), the bank client and any POS or fiscal-device integration; the Russian-market equivalents (Честный знак, Меркурий, ЕГАИС, ФГИС Зерно) apply only in that jurisdiction · volumes: total and concurrent users, SKU count, documents per day and month by type, average lines per document, current database size, how much history is to be migrated · equipment: servers, handheld terminals, scanners, cash registers, label printers, scales.

The volume numbers are the ones most often skipped and most often decisive. They drive licence count, hardware, migration effort and every performance requirement in the specification — and they are free to collect while you are already there.

## The interview question bank

*A. Goals* — what the company does, its lines of business, seasonality · why we are implementing: what pain, what measurable result, what counts as success · which processes must not stop · who is the sponsor, who owns each process, who decides disputes · which deadlines are hard (reporting, season, contract, legislation).

*B. Organization and accounting perimeter* — how many legal entities and tax regimes, any branches · is management accounting kept separately from regulated accounting, and where do the two diverge · accounting currency, foreign trade, multi-currency · ЦФО and budget items; is there budgeting.

*C. Purchasing* — how a need arises (заявка, plan, reorder point, MRP) · who approves and against what limits · additional costs, imports, customs declarations, tolling · how settlements are tracked: by contract, order or delivery note; advances and offsets.

*D. Sales* — customer segments, price types, discounts and who approves them · reservation, shipment, commission, returns · credit limits and receivables control · marking, electronic document exchange, cash operations.

*E. Warehouse* — how many warehouses, order scheme or not, addressed storage · units of measure, packaging, batches, series, shelf life · stocktaking frequency and how mis-sorting is recorded · internal transfers, kitting.

*F. Production* — type (to-order, serial, process) · resource specifications, routings, norms — in what form do they exist today · how planning works and the horizon · output, scrap, deviation from norms · costing methodology and the allocation base for indirect costs.

*G. Finance and treasury* — payment calendar, payment requests, approval · bank client, acquiring, expense accountability · settlements and reconciliations.

*H. Regulated accounting and HR* — учётная политика specifics; **what is done by hand in Excel during period close** (this question is worth ten others) · HR, schedules, payroll, special regimes.

*I. Master data* — who owns each catalog, is there an entry regulation · naming and coding rules, duplicate control · how many records, what share is junk or historical.

*J. Integrations* — systems, direction, object, frequency, volume · who is master for each entity · what happens on failure and who is responsible.

*K. Reporting* — which reports are read daily, weekly, monthly; who receives each and **what decision is made from it** · attach the real files.

*L. Non-functional* — target response time, target period-close duration · working hours, maintenance windows · information security, access segregation, personal data.

A standard 1C implementation questionnaire runs to around 66 questions and works well as a first diagnostic pass.

## Описание AS-IS for a 1C project

Notations in use: функциональные блок-схемы, IDEF0, EPC, BPMN. In practice: **IDEF0** for the top level and boundaries, which reads well for executives; **BPMN** for end-to-end processes with roles as lanes and decision points — and describe it **down to the specific system documents**, which is explicitly recommended as the counter-measure to the "incomplete requirements" risk; **EPC** when the customer already lives in ARIS or Business Studio.

The most useful format for 1C work is a table, one row per process step:

`№ · Действие · Роль · Вход (документ/данные) · Выход · Система · Объект 1С · Частота · Трудоёмкость · Проблема/боль · Требование (ID)`

The **Объект 1С** column is what makes this different from generic process modelling: every step is bound to a concrete metadata object, which is how you find out that two steps everybody described separately are actually the same document, or that a step nobody mentioned has no object at all.

## Обследование report structure

1. Общие сведения — customer, contractor, basis, period, participants, interviews and протоколы held
2. Цели и задачи проекта, ограничения и допущения
3. Краткая характеристика предприятия — activities, org structure, legal entities, headcount, volumes
4. Текущее состояние (AS-IS) by block — process, systems and documents used, problems and bottlenecks
5. Реестр видов документов и процессов, подлежащих автоматизации
6. **Реестр требований** — ID, formulation, source, block, priority, status
7. Оценка текущего состояния НСИ и план нормализации
8. ИТ-ландшафт: текущий и целевой; systems to integrate; master systems per entity
9. Исторические данные и способ их переноса
10. Рекомендации по изменению порядка ведения учёта
11. Предложения по программной и технической архитектуре — which 1C products, which licences, server requirements
12. План развёртывания — which blocks in which order and by when
13. Выбранная методология проектного управления
14. **Измеримые результаты проекта** — success criteria
15. Ресурсы, требуемые от обеих сторон, including key users' time
16. Бюджет и укрупнённый план-график
17. Риски и допущения
18. Приложения — blank forms, regulations, AS-IS diagrams, interview протоколы

Section 15 is the one customers skip and then resent: key users' time is the scarcest resource on the project, and naming the number of days per person up front is what prevents the classic mid-project collapse.

## Fit-gap and the decision hierarchy

Each requirement is **Fit** (the standard configuration already does it) or **Gap** (needs configuration or development). Classify each gap with **RICEFW** — the ERP-standard scheme (Reports, Interfaces, Conversions, Enhancements, Forms, Workflows; also written RICEF or WRICEF) — plus an **S** category for pure configuration, which matters in 1C because so much of the work lands there. Add complexity and an estimate of reuse:

| RICEFW+S | Meaning | How it lands in 1C | Support impact |
|---|---|---|---|
| **S** — System configuration | Settings | Функциональные опции, параметры учёта и учётная политика, **дополнительные реквизиты и сведения**, профили групп доступа, варианты отчётов СКД, правила ценообразования, регламентные задания | None — configuration stays standard |
| **R** — Report | Report | Вариант типового отчёта → внешний отчёт (.erf) via БСП → отчёт в расширении → отчёт в конфигурации | .erf or extension keeps support |
| **F** — Form | Printed form | Макет via «Управление печатными формами» БСП → внешняя печатная форма (.epf) → макет в расширении → изменение типового макета | .epf or extension keeps support |
| **C** — Conversion | Migration | Конвертация данных 2.1/3.0, external data processors | Usually outside the configuration |
| **I** — Interface | Integration | HTTP/web services, EnterpriseData, планы обмена, external data sources, file exchange | Some objects can't live in an extension |
| **E** — Enhancement | Logic change | Расширение (&Перед / &После / &ИзменениеИКонтроль) → правка типового модуля → новый объект | **The key decision point** |
| **W** — Workflow | Approval and routing | Бизнес-процессы и задачи, БСП согласование, маршруты в 1С:ДО | Usually configuration plus an extension |

**The decision hierarchy — the central algorithm of this whole file:**

```
0. Change the business process to fit the standard      ← always consider first
1. Configuration (функц. опции, параметры учёта, права,
   доп. реквизиты, варианты отчётов, правила обмена)     → support untouched
2. External objects (.epf / .erf via БСП)                → support untouched
3. Configuration extension (.cfe)                        → configuration stays locked
4. Modifying a standard object "с сохранением поддержки" → manual merge on every update
5. A new own object in the configuration                 → same support mode as 4; the
                                                           object itself never conflicts
6. Full removal from support                             → updates by developers only
```

Levels 4 and 5 land in the **same support state**: both require enabling «Возможность изменения», which moves the configuration root to «редактируется с сохранением поддержки». What separates them is how much vendor code you then merge by hand at each release: a *modified* standard object must be reconciled every time the vendor changes it, while a brand-new object of yours has no vendor counterpart and never conflicts. So the real cost driver is not the step number but **how many vendor objects you touch** — and that is the sentence to say out loud in the meeting, because the customer is comparing implementation quotes and the difference lives in total cost of ownership, not in the quote.

Step 0 deserves real consideration rather than lip service. "Change the process" is often cheaper, faster and better — the standard configuration encodes a working practice, and the customer's current process is frequently an accident of what their old system could do. But it is also the option with the highest change-management cost, so present it with that cost visible rather than as the obviously correct answer.

**Three implementation approaches, as you would frame them for a sponsor:**

| Approach | When | Budget | Updatability |
|---|---|---|---|
| Типовое внедрение | Processes are close to standard | Minimal, short | Simplest possible |
| Внедрение с доработками | Most processes fit; some need development | Grows with development volume | Compatibility check at every update |
| Разработка под требования бизнеса | The standard model doesn't fit key processes | Maximum, longest | Needs its own update strategy |

The decision procedure: identify the current process → compare with the system's capability → document the divergence → assess the architectural consequence → recommend.

## Support modes and what they cost

| Mode | Meaning | Consequence |
|---|---|---|
| **Объект поставщика не редактируется** | Default; editing must be enabled per object | Everything else stays protected; cheapest updates |
| **Редактируется с сохранением поддержки** | Can be changed, keeps the link to the vendor configuration | **Manual compare and merge at every release** |
| **Снят с поддержки** | The link is broken entirely | Automatic update impossible; not recommended |

Once a vendor object is actually modified, that object can no longer be updated automatically — its merge is manual at every release. In economic terms: extension-based changes usually absorb a vendor update with no conflicts or minimal divergence, while direct modification requires manual comparison, merge and retest **for every release**, and rollback is often impossible.

## Extensions: what an analyst must know

One thing to settle before routing a gap to level 2: external reports and data processors connected through БСП's «Дополнительные отчёты и обработки» normally run in **безопасный режим**, which blocks privileged operations, file-system access and COM. If the requirement needs any of those, level 2 is not available — record that in the gap register rather than discovering it in development.

**Extensions suit:** hotfixes without waiting for a release · temporary solutions, including cloud bases where direct modification is impossible · added forms, reports, data processors, commands and interface changes · integrations and event subscriptions instead of editing standard code · long-lived systems that update regularly.

**Extensions suit badly, or not at all:** new permanent objects holding business-critical data (catalogs, documents, registers — that data belongs in the main configuration) · changing metadata types or field types in the core · fully reworking complex algorithms, since some modules are protected at vendor level · a set of object types that simply cannot be created in an extension, which varies by platform version and must be checked against the target release.

**Risks to put in the risk register in writing:**
- **Deleting an extension destroys the data stored in it, irreversibly.** Disabling keeps it; deleting does not. This is the one that produces a genuine catastrophe.
- `&Вместо` creates compatibility problems on update — prefer `&Перед`, `&После`, `&ИзменениеИКонтроль`.
- Form changes in an extension produce **no warning** on update — silent failures.
- After an update the vendor may have changed the objects an extension relies on, and the extension stops working.
- Storing data in an extension performs worse than in the main configuration.
- Many small extensions make administration disproportionately harder. Consolidate related changes into one, and keep a **register of extensions** describing every modification.

## The gap register

`ID · Блок/подсистема · Требование · Источник · Бизнес-обоснование · Типовой аналог · Вердикт: FIT / GAP / FIT-with-process-change · RICEFW+S · Способ реализации · Затрагиваемые объекты метаданных · Влияние на режим поддержки · Трудозатраты (O/M/P, PERT) · Приоритет (Must/Should/Could/Won't) · Волна/релиз · Риски · Статус · Решение принял`

Two columns carry more weight than the rest. **Влияние на режим поддержки** is the total-cost-of-ownership column, and it is the one a sponsor should read. **Решение принял** is what stops the same gap being reopened every month by whoever lost the argument.

The most effective way to *find* gaps is not interviewing but **prototyping and demonstration** — showing a working configuration or screen mockups along end-to-end process chains. People recognize what is wrong far faster than they can describe what they need.

## Постановка задачи разработчику

The document chain, and who reads each:

| Document | Audience | Level |
|---|---|---|
| **ТЗ / Проектное решение** | Customer (contract) | What we are doing overall, boundaries, acceptance criteria |
| **ФТ** — функциональные требования | Customer and team | How it will look and behave, **in business language, without platform terms** |
| **ЧТЗ** — частное техническое задание | Developer and key users | Detail per block: objects, attributes, algorithms, roles, schedules |
| **ЗНР** — задание на разработку | One developer | An atomic task in the tracker |

The practitioner's analogy: ТЗ is the constitution, ЧТЗ are the codes.

**Reference structure for a 1C development task** — this is the single most reusable artifact in this file; the template is in `assets/1c-task-spec-template.md`:

1. **Паспорт задачи** — ID · name · initiator with contacts · author · date · desired deadline · **priority** · configuration and its **release** · platform version · base (prod/test) · linked requirement IDs · link to the ПР/ЧТЗ
2. **Основание и бизнес-цель** — the user story · what happens today and why it's bad, **in numbers** · how we will know the goal was met
3. **Описание бизнес-процесса** — AS-IS briefly, TO-BE with the new function's place in it, roles, frequency, volume
4. **Границы задачи** — what's in · **what is explicitly out** · assumptions · dependencies
5. **Способ реализации** — the chosen level from the decision hierarchy · the **exact metadata path** (`Документ.РеализацияТоваровУслуг`, its form) · effect on support mode · what must not be touched
6. **Описание объектов метаданных** — see below
7. **Формы** — wireframe, placement, behaviour (availability, visibility, field dependencies), handlers, behaviour on copy and on ввод на основании, **exact message texts**
8. **Печатные формы** — a sample in Word/Excel with **green fields** marking auto-filled places, numbered, and **red comments** naming the data source for each. Checklist: repeating blocks, grammatical declension, name format, page numbering, signatures and stamps, number of copies, output format
9. **Отчёты** — name, section and menu item · purpose as a user story · **data sources** · logic, best expressed as a pseudo-query ("balance on register X by dimension Y as at date Z") · user settings, filters, periods · visual layout with groupings, sortings, totals · **a control example with test data and expected result on the working base**
10. **Алгоритмы** — in descending order of preference: a flowchart for complex logic → a query or pseudo-SQL → prose for the simple cases. Always describe: fill algorithm (default, on ввод на основании, on attribute change); **posting algorithm** — which movements to which registers, with which dimension and resource values, the **sign** (приход +, расход −), and the formulas; **checks during posting** — what is verified, the exact error text, and whether it blocks or warns; **unposting, re-posting**, effect on sequences; behaviour on deletion or marking for deletion
11. **Права доступа и RLS** — which roles get which rights (read/add/change/delete/post), record-level restrictions by organization, warehouse, subdivision, ЦФО, and **who must not see it**
12. **Обмен / интеграция** — direction · counterpart system · **master of data** · transport · format and schema · **the transferred data, object by object and field by field** · the matching rule (by code, tax ID, GUID) · frequency and window · volume · error handling and resend · logging · who monitors
13. **Нефункциональные требования** — target operation time, concurrent users, expected volumes, multi-user behaviour and locking, action logging, audit
14. **Влияние на существующие данные** — is a data processor needed to fill a new attribute in historical records; is re-posting required; downtime window; rollback order
15. **Сценарии приёмки** — the control example table
16. **Документация и обучение**
17. **Лист согласования** — analyst · PM · architect · process owner · **developer, confirming the task is understandable and estimated**

**Describing attributes.** The table needs these columns:

`Имя (идентификатор) · Синоним · Тип · Длина/Точность · Обязательность · Значение заполнения · Связи · Индексировать · Видимость · Доступность · Комментарий`

And the rules that make the difference between a spec a developer can build from and one they have to come back about:

- **Type must be concrete.** "Строка" without a length is not a type. For reference types name the object exactly: `СправочникСсылка.Контрагенты`.
- **Composite types** must list their composition explicitly — and note that they degrade query performance, so use them deliberately rather than by default.
- For `Строка`, say whether the length is fixed or variable, and flag **unlimited length** explicitly, because it affects indexing and queries. For `Дата`, state the **состав даты**: Дата, Время, or Дата и время.
- **Обязательность** is phrased as «Проверка заполнения = Выдавать ошибку», plus **when** it is checked — on write, or on posting.
- Distinguish `Значение заполнения` (the property) from algorithmic filling on creation.
- **Связи** — say which is meant: `Параметры выбора` (a fixed filter), `Связи параметров выбора` (a filter depending on another field), `Связь по типу` for composite types.
- Ask for an **index** explicitly where the field will be filtered or searched, and justify it.
- For every attribute, name the **source of the value**: entered by the user, filled by an algorithm, arrives from an exchange, or calculated.

**Registers** need their own table. Information register: periodicity (non-periodic, or within second/day/month/quarter/year), write mode (independent or subordinate to a recorder), **dimensions** with the leading flag, **resources**, attributes, main filter. Accumulation register: **остатки or обороты**, dimensions, resources, attributes, and the list of recorders. Accounting register: chart of accounts, correspondence, dimensions, resources, accounting flags and subconto.

**Anti-patterns in постановка задачи**, worth checking your own draft against: repeating the same content in different sections with different wording · unstructured order instead of grouping by process or module · uneven depth between sections · contradictions between sections · exhaustive detail on one element and silence on the rest · abstract phrasing like "take the customer's debt" instead of "calculate the balance on register X by dimension Y". And from the customer's side: writing technical specifications (buttons, attributes, algorithms), modelling processes on the contractor's behalf, designing the 1C solution, and choosing licences alone.

A well-written task is not a formality: the same management-report task runs **25–35 hours from a poor specification against 5–8 hours from a good one**. That is the number to quote when someone proposes skipping this step to save time.

## Приёмка: ПМИ, test scenarios, контрольный пример

**Types of testing** for an automated system: предварительные автономные (parts against the ТЗ) · предварительные комплексные (components together) · опытная эксплуатация (real conditions) · приёмочные испытания (the final gate).

**ПМИ — программа и методика испытаний**, nine sections: объект испытаний · цель испытаний and the list of qualities being verified · общие положения · объём испытаний · условия и порядок проведения · материально-техническое обеспечение · метрологическое обеспечение · отчётность · **приложения with the step-by-step test methods**. Outputs: протоколы, акт испытаний, единый протокол приёмочных испытаний.

The ПМИ must cover **every functional and non-functional requirement in the ТЗ** with its expected result. For the customer it is the last opportunity to influence the system's characteristics, which is worth saying to them plainly.

**Checks analysts routinely forget:** deploying the software from scratch · full and partial recovery · response time of key functions (a 3-second benchmark) · resilience to a dropped and restored connection · completeness of documentation · conformity of software and hardware with the ТЗ · load testing with N concurrent users. And: **run the tests on data volumes comparable with a planned year**, generating data automatically where necessary. A system that passes acceptance on twenty documents and fails in March is a specification failure, not a development failure.

**Test scenario table:**

`ID · Требование (ID) · Бизнес-процесс · Роль · Предусловия (состояние базы, НСИ, остатки) · Шаг · Действие · Исходные данные (concrete values) · Ожидаемый результат (concrete numbers, statuses, register movements) · Фактический результат · Статус · Замечание · Приоритет дефекта · Дата, ФИО`

The rule: the expected result must be **checkable**. Not "the report is generated correctly" but "in the warehouse A report as at 31.03, quantity = 150 units, amount = 1,500,000; the row 'Товар Б' is absent".

**Контрольный пример** is the decisive acceptance artifact in 1C work, because in an accounting system correctness is not a property of the interface but of **whether the numbers reconcile** — balances, cost, settlements, tax. No UI test shows that.

How to build one:

1. Choose a **closed** period, usually a month, for which the customer has signed reporting. That signed reporting is your reference answer.
2. Record the **opening balances** at the start of the period, across every dimension: warehouses, counterparties, contracts, accounts.
3. Select a **representative** set of operations: the typical ones *plus every hard case* — returns, mis-sorting, commission, imports with customs declarations, tolling, scrap, retro-discounts, partial payment, advance offset.
4. For each operation, write out the input data and the **expected movements** across registers and the expected accounting entries.
5. Compute the expected totals: оборотно-сальдовая ведомость, balances in quantity and amount, unit cost, settlements by counterparty, VAT, financial result.
6. Run the whole scenario in the new system, **including period close**.
7. Compare with the reference, and classify every divergence as: a system defect / an error in the source data / a **methodological divergence** — the new system computes differently and is right, which gets its own written decision agreed with the chief accountant.
8. Produce a **Протокол контрольного примера** with the divergence table and the decisions.

Mandatory contents: period · list of operations · opening balances · the operation → expected entries table · the list of control reports with expected values · the tolerance (for instance, kopeck rounding) · the names of the business people who signed off.

**Managing ОПЭ:** the artifacts are the **рабочий журнал ОПЭ** (every event, problem and action in real time), **акт устранения замечаний**, **протокол приёмочных испытаний**, and a plan for the remaining non-critical items. The exit criterion is condition-based, not date-based: no open error reports and all justified functional requests fulfilled.

**1C-specific test tooling:** Vanessa-Automation, xUnitFor1C, 1С:Сценарное тестирование, and the БСП mechanisms. Selenium is a poor fit — the web client's generated DOM makes selectors fragile, so prefer the 1C-native tools above. **Typical 1C defect classes** to design tests around: integration (format mismatch, API changes producing duplicated orders), performance (slow reports, hanging forms), access-rights errors, migration and update failures, business-logic errors in tax, discounts and commission, and defects in reports and printed forms.

## Estimation

**PERT**, which is the working method on 1C projects:

- Expected: `E = (O + 4M + P) / 6`
- Standard deviation: `σ = (P − O) / 6`
- Risk coefficient: `CV = σ / E` — **above 20% means the estimate needs rework**, not a bigger buffer
- Project total with buffer: `Σ E + 2 · √(Σ σ²)` — the deviations of independent tasks add **in quadrature**, not linearly. Summing σ directly inflates the buffer by roughly √n (with 25 tasks, about fivefold) and the confidence label then means nothing. Use `1.645 · √(Σ σ²)` for ≈95% one-sided, `2 · √(Σ σ²)` for ≈98%.

What the three points mean matters: **optimistic** is "we certainly cannot do it faster"; **realistic** includes the usual interference; **pessimistic** is built on **documented risks**, not on free-floating gloom. An analyst who invents the pessimistic number has produced a decorative estimate.

Practical guidance: keep σ ≤ 2 (more means insufficient decomposition) · decompose to atomic tasks of about **8 hours** · for risky technical points run a **20–30 minute micro-test** — a probe, not an implementation · reserve **5–15%** for rework cycles. And include the hidden effort everyone forgets: estimating the task itself, code review, first-pass testing, and rework after review; for functional specialists, also requirements analysis and coordinating acceptance testing.

**Estimate accuracy by stage** — say which stage you're at whenever you give a number:

| Stage | Basis | Accuracy |
|---|---|---|
| Presale / экспресс-обследование | Questionnaire, analogues | ±30–50% |
| After ППО, requirements register and fit-gap | Each gap by RICEFW+S, complexity, reuse | ±15–20% |
| After ЧТЗ | Decomposed to atomic tasks, PERT | ±10% |
| After functional modelling | Prototype on the standard plus agreed ЧТЗ | ±5% — residual variance is rework and integration |

The commercial practice that follows: **fix the commercial proposal at the ФТ level and refine the development budget at ЧТЗ**, with the transition formalized as a contract amendment. Quoting a fixed price from a questionnaire is how projects arrive at their first crisis.

Rough single-task benchmarks, as a sanity check rather than a price list: a new report from 2 hours · modifying an existing report or printed form from 1 hour · a new document with form, printed form and posting nominally from 1 hour but realistically much more · data exchange between 1C bases from 1 hour to several days · importing from Excel/dbf from 6 hours. Note the industry observation that even the simplest functional specification takes 4–7 person-days end to end including specification, development and module testing — under-estimating here just moves the defect downstream.

**Project roles:** руководитель проекта · функциональный архитектор/методист · консультант/бизнес-аналитик по подсистеме · системный аналитик · архитектор решения/ведущий разработчик · разработчики · тестировщик · специалист по миграции и НСИ · администратор 1С/DBA · менеджер по обучению. On the customer side: спонсор, куратор, владельцы процессов, ключевые пользователи, суперпользователи, ИТ-служба. The governance structure is управляющий комитет · проектная команда исполнителя · рабочая группа заказчика.

## Data migration and master data

**Planning, in eight steps:** agree the go-live date, the depth of history and the schedule → work out the data structure (what has to appear in operational, regulated and management accounting) → assess completeness and volume → decide the loading sequence → choose the method per entity (automatic, manual, combined) → **agree the reconciliation method before transferring anything** → build the plan with named owners → run the organizational measures (templates, stocktaking, date synchronization).

What moves: catalogs in full, balances (stock, settlements), and documents (closed, open, primary). Methods: Конвертация данных rules, manual entry via documents, or a combination.

**Master data preparation, in nine steps:** audit and inventory (export the catalogs, count duplicates and empty mandatory fields) → classify each record as transfer / merge / clean / archive / exclude → unify naming and fill mandatory fields → deduplicate using «Поиск и удаление дублей», matching on tax ID or article → build **old→new mapping tables** (for example УПП cost items → ERP cost items) → prepare the export → **run a test export-import on a limited set** → design the reconciliation procedures → set up quality metrics and an ongoing regulation.

For номенклатура specifically, the normalization work is its own project: analyze the group structure; move unplanned parameters into серии; normalize only the groups that drive requirement planning and exclude the "warehouse accounting only" groups; separate out historical positions with zero balances and no presence in specifications into their own group with restricted selection; deduplicate, with **engineering rather than the analyst deciding physical identity**; reconcile the specification and warehouse item lists; link supplier names to the leading item; define auto-assembly rules for names; consider faceted grouping instead of deep hierarchy; define the article system; and establish the **approval process for changing item attributes**. The quality criteria at the end: every position unique, no historical positions, names structured by a formula, identical items in specifications and accounting, and unique codes.

**Opening balances in 1C** — a mechanic the analyst needs in the plan: the balance entry date is single for all entry documents and **precedes** the start date of live work, typically the last day of the preceding month. Entries are made against account 000, and the **check is that the balance on account 000 is zero**.

**Reconciliation checklist after migration:**

*Formal:* balance on account 000 = 0 · оборотно-сальдовая ведомость of the new base against the old system on the transfer date, per account, in currency and quantity · control totals on the export/import — record count, sums of key numeric fields, rejected rows and why · no broken references and no empty mandatory attributes.

*Substantive:* stock by warehouse in quantity **and** amount, separately by batch, series and characteristic · settlements by counterparty, contract and settlement document, with advances given and received separately · open customer and supplier orders, reservations · work in progress, semi-finished goods, tolling stock · fixed assets and intangibles — initial cost, accumulated depreciation, term and method · cash at bank and in hand · VAT — purchase and sales ledgers, unconfirmed VAT, advances · HR and payroll — headcount, leave balances, deductions, wage liability · cost — reconciliation after the **first period close in the new system**.

*Process:* at least **two or three full test migration waves** before the real one, each with a divergence protocol · a **mock cutover** rehearsing the transition with each step timed · a **cutover plan** by the hour — stop entry in the old system → final export → import → reconcile → open access — with go/no-go decision points and a rollback plan · a **протокол проверки начальных остатков** signed by the chief accountant and the process owners.

Migration is where up to 30% of overrun time goes on late projects, and the reason is almost always that reconciliation was designed after the transfer rather than before it.

## The risk register

| Risk | Consequence | Mitigation |
|---|---|---|
| **Go-live not on 1 January** | Documents carried over with their numbers preserved; quarterly reporting by hand; mid-month balance corrections | Go live at a period boundary; launch subsystems in sequence |
| **Business processes changing during ОЭ** | ОЭ never finishes; production entered with unsettled processes | Launch with modelled processes and refine later; sequenced launch; exchange with the old system |
| **No or incomplete process description** | Incomplete requirements, growing effort and schedule | Describe in BPMN **down to the documents**; test runs before launch; split genuinely complex processes into their own project |
| **Multiple contractors plus customer-side work** | Boundaries blur, responsibility unclear | Synchronize, hold schedules firmly, direct contractor-to-contractor contact, an **architecture committee** to agree specifications |
| **Users didn't absorb the training** | Around 30% of data can't be entered during ОЭ; shipments delayed; rollback to the old system | Follow the training plan; **check comprehension every 2–3 days**; build a competence centre from key users |
| **Integrator misunderstood the task** | Wrong products implemented | Describe the pain honestly; extend the survey; test runs on real data |
| **External and regulatory systems change their schema** — for a Georgian client the RS.ge services (სასაქონლო ზედნადები / waybills, ანგარიშ-ფაქტურა / e-invoices, VAT reporting) and the bank client; in the RF market Честный знак, Меркурий, ЕГАИС | Integrations break, disputes about who pays | **Record the schema and release version in the project documentation**; monitor announced changes; hold a risk reserve |
| **No project team on the customer side** | Key users won't take decisions; schedule slips | A proactive PM with authority; mandatory key-user involvement; respond to the integrator's warning signals |
| **Insufficient server capacity** | Period close takes a day instead of 2–4 hours; lock conflicts | Assess hardware against 1C's recommendations early; a hardware questionnaire; buy, rent, or postpone |

The six recurring causes of ERP failure, of which roughly 60% of projects miss their goals: insufficient pre-project analysis · excessive customization · neglected data migration · resistance to change · insufficient training · insufficient post-launch support.

Resistance to change deserves naming explicitly because analysts tend to treat it as somebody else's problem. It has three distinct sources — fear that existing skills become worthless, the increase in transparency (a new system exposes the workarounds people relied on), and a real increase in workload during parallel running. Only the third is solved by scheduling. The first two are solved by what people are told about their role, and by who is asked to help design the new process.

Post-launch targets worth writing into the plan: under 0.5% critical failures, availability ≥99.5%, document posting in 3–5 seconds, and at least 60% functional utilization within three months. The first three to six months after go-live are the ones that decide whether the system is adopted or worked around.

## Sources for the figures in this file

The numbers quoted above are practitioner reporting and industry rules of thumb, not measured statistics from a controlled study. Cite them that way, and if a sponsor is about to make a decision on one, say so.

- 1C methodologies (ТСВ / ТБР / ТКВ / ТКЛ / ТКС), phases and roles — `consulting.1c.ru/technologies/`, `1c.ru/uk-part/uk/qual/technology`; the spiral deliverables table follows D. Stepanov's peer-reviewed survey of ТКВ output by phase.
- Обследование types, durations and estimate bands; the 200–220 specialist-hour benchmark — practitioner accounts from 1C implementation firms (habr.com, erp-it.ru, gigansk.ru).
- Fit-gap, RICEF/RICEFW classification and the traceability matrix — `corpinfosys.ru` (2018, issue 2).
- Support modes, extension limits and the update economics — 1C partner publications (tnsoft.ru, legasoft.ru, tpl-soft.ru, itkonus.ru, stekspb.ru).
- The "under 20% customization" and "15–20% of project time on analysis" rules of thumb, and the 60%-of-ERP-projects-miss-goals figure — klerk.ru practitioner analysis.
- The 25–35h vs 5–8h specification-quality comparison — kvant-c.ru, from one firm's own task data.
- PERT practice in 1C projects, decomposition and reserve guidance — infostart.ru/pm/2645163. **The buffer formula here is corrected**: the source sums σ linearly, which overstates the buffer; independent deviations add in quadrature.
- ПМИ structure and acceptance practice — babok-school.ru, ecm-journal.ru; ГОСТ 34.601-90, ГОСТ 34.603-92 / ГОСТ Р 59795-2021, РД 50-34.698-90.
- Migration, НСИ normalization and the reconciliation checklist — sb-vnedr.ru, nfp2b.ru, itrp.ru, 1cbit.ru.
- Risk register — 1ccl.ru, assino.ru.

## Handing off to the 1c-developer skill

Know where your work stops. This skill produces the **decision and the specification**: which metadata objects, which attributes with types and rules, which register movements with signs and formulas, which roles and restrictions, which acceptance scenarios. It does **not** write BSL, design the module structure, or build the XML.

When the conversation moves to implementation — writing the `ОбработкаПроведения`, optimizing a query, building the extension, packing an .epf — hand off to the **1c-developer** skill if it is available in the session, and say so in one line. If it isn't available, say that the implementation is out of this skill's scope and offer the specification as the handoff artifact rather than improvising code.

The handoff is clean when the developer can start without asking you anything: exact metadata path, exact types, exact register movements with signs, exact message texts, the roles matrix, and the control example they can test against. If they have to come back with a question, that question belongs in the next version of your template.
