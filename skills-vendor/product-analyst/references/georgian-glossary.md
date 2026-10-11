# Georgian Terminology & Output Templates (ქართული ტერმინოლოგია)

Use this to keep Georgian output natural and consistent. Georgian-speaking analysts and product managers routinely mix in the canonical English term — and, in 1C/ERP work, the canonical Russian one — so the right register is **clear Georgian prose with the established term kept alongside**, usually in parentheses the first time it appears. A forced calque nobody uses is worse than the borrowed word.

Three rules that decide whether the output reads as professional or machine-translated:

1. **Name the concept in Georgian, keep the canonical term in parentheses on first use**: `მიღების კრიტერიუმები (acceptance criteria)`, `ხარვეზების რეესტრი (реестр GAP)`. After the first mention, the Georgian alone is fine.
2. **Never translate an identifier.** Metadata names, register names, requirement IDs, document codes and standard clause numbers stay exactly as they are: `Документ.РеализацияТоваровУслуг`, `ГОСТ 34.602-2020 §4.6.2`, `R-014`. A translated identifier is unusable by the person who has to act on it.
3. **Keep the ГОСТ section titles in Russian** next to their Georgian heading when the document must pass a formal review — committees look for the numbering and the familiar wording.

## Reusable section headings

**Specification mode:**

- `## პრობლემა და კონტექსტი` — problem and context
- `## სასურველი შედეგი` — desired outcome
- `## სამიზნე მომხმარებელი` — target user / audience
- `## მოცულობა` — scope
- `## რა რჩება მიღმა` — non-goals / out of scope
- `## ბიზნეს-პროცესი: არსებული მდგომარეობა` — AS-IS
- `## ბიზნეს-პროცესი: სამიზნე მდგომარეობა` — TO-BE
- `## ფუნქციური მოთხოვნები` — functional requirements
- `## არაფუნქციური მოთხოვნები` — non-functional requirements
- `## მომხმარებლის ისტორიები` — user stories
- `## მიღების კრიტერიუმები` — acceptance criteria
- `## მონაცემთა სტრუქტურა` — data structure
- `## უფლებები და წვდომა` — rights and access
- `## ინტეგრაციები` — integrations
- `## წარმატების მეტრიკები` — success metrics
- `## დაშვებები და რისკები` — assumptions and risks
- `## ღია კითხვები` — open questions
- `## გადაწყვეტილებების ჟურნალი` — decision log

**Discovery mode:**

- `## აღმოჩენის შეჯამება` — discovery summary
- `## მტკიცებულებები` — evidence
- `## შესაძლებლობები` — opportunities
- `## ჰიპოთეზები და დაშვებები` — hypotheses and assumptions
- `## რისკიანი დაშვებები` — riskiest assumptions
- `## შემოწმების გეგმა` — validation plan
- `## პრიორიტეტების ცხრილი` — prioritization table
- `## რანჟირება და დასაბუთება` — ranking and rationale
- `## დაინტერესებული მხარეები` — stakeholders

**Review mode:**

- `## შეფასების შეჯამება` — review summary
- `## 🔴 კრიტიკული` / `## 🟠 მნიშვნელოვანი` / `## 🟡 მცირე` / `## 🟢 რეკომენდაცია`
- `## რა არის კარგად` — what's done well

**Markers used inline:**

- `[დასაზუსტებელია: <what is missing>, <who can answer>]` — an unknown. Never replace this with an invented value.
- `[შეფასება]` — an estimated rather than measured figure.
- `[წყარო: <where it came from>]` — the evidence behind a claim.

## Terminology table

### Product management

| Concept | Georgian | English / canonical |
|---|---|---|
| Product manager | პროდუქტის მენეჯერი | Product manager |
| Business analyst | ბიზნეს-ანალიტიკოსი | Business analyst |
| Discovery | აღმოჩენა, კვლევითი ეტაპი | Discovery |
| Outcome | შედეგი (outcome) | Outcome |
| Output | მიწოდებული პროდუქტი (output) | Output |
| Opportunity | შესაძლებლობა | Opportunity |
| Hypothesis | ჰიპოთეზა | Hypothesis |
| Assumption | დაშვება | Assumption |
| Evidence | მტკიცებულება | Evidence |
| Prioritization | პრიორიტიზაცია | Prioritization |
| Roadmap | საგზაო რუკა (roadmap) | Roadmap |
| Release plan | გამოშვების გეგმა | Release plan |
| Metric | მეტრიკა, მაჩვენებელი | Metric |
| Baseline (metric) | საბაზისო მნიშვნელობა | Baseline |
| Guardrail metric | დამცავი მეტრიკა | Guardrail / counter-metric |
| Leading / lagging indicator | წინმსწრები / შემდგომი ინდიკატორი | Leading / lagging indicator |
| Experiment | ექსპერიმენტი | Experiment |
| Trade-off | კომპრომისი (trade-off) | Trade-off |

### Requirements

| Concept | Georgian | English / Russian |
|---|---|---|
| Requirement | მოთხოვნა | Requirement / требование |
| Business requirement | ბიზნეს-მოთხოვნა | Business requirement / бизнес-требование |
| Stakeholder requirement | დაინტერესებული მხარის მოთხოვნა | Stakeholder requirement |
| Functional requirement | ფუნქციური მოთხოვნა | Functional requirement / функциональное требование (ФТ) |
| Non-functional requirement | არაფუნქციური მოთხოვნა | Non-functional requirement / НФТ |
| Transition requirement | გარდამავალი მოთხოვნა | Transition requirement |
| Requirements register | მოთხოვნების რეესტრი | Requirements register / реестр требований |
| Traceability | მიკვლევადობა | Traceability / трассируемость |
| Baseline (document) | დაფიქსირებული ვერსია | Baseline |
| Scope | მოცულობა | Scope |
| Out of scope | მოცულობის გარეთ | Out of scope |
| Scope creep | მოცულობის უკონტროლო ზრდა | Scope creep |
| Constraint | შეზღუდვა | Constraint / ограничение |
| Glossary | ტერმინთა ლექსიკონი | Glossary / глоссарий |
| Specification | სპეციფიკაცია | Specification / ТЗ, ЧТЗ |
| Verification | ვერიფიკაცია, გადამოწმება | Verification |
| Validation | ვალიდაცია, დადასტურება | Validation |

### Backlog and delivery

| Concept | Georgian | English |
|---|---|---|
| Epic | ეპიკი | Epic |
| Feature | ფუნქცია, შესაძლებლობა (feature) | Feature |
| User story | მომხმარებლის ისტორია | User story |
| Acceptance criteria | მიღების კრიტერიუმები | Acceptance criteria |
| Backlog | ბექლოგი | Backlog |
| Definition of Ready | მზაობის კრიტერიუმები | Definition of Ready |
| Definition of Done | დასრულების კრიტერიუმები | Definition of Done |
| Spike | კვლევითი დავალება (spike) | Spike |
| Estimate | შეფასება | Estimate / оценка |
| Effort | შრომატევადობა | Effort / трудозатраты |
| Sprint / iteration | სპრინტი, იტერაცია | Sprint / iteration |
| Defect | დეფექტი | Defect / дефект, замечание |

### Process and modeling

| Concept | Georgian | English / Russian |
|---|---|---|
| Business process | ბიზნეს-პროცესი | Business process / бизнес-процесс |
| AS-IS state | არსებული მდგომარეობა | AS-IS / «как есть» |
| TO-BE state | სამიზნე მდგომარეობა | TO-BE / «как должно быть» |
| Process step | პროცესის ნაბიჯი | Process step |
| Role | როლი | Role |
| Swimlane | ბილიკი / ზოლი (lane) | Lane / дорожка |
| Gateway | გადაწყვეტილების წერტილი | Gateway |
| Use case | გამოყენების შემთხვევა (use case) | Use case |
| Decision table | გადაწყვეტილების ცხრილი | Decision table / таблица решений |
| State diagram | მდგომარეობათა დიაგრამა | State diagram |
| Entity | არსება (entity) | Entity / сущность |
| Data model | მონაცემთა მოდელი | Data model |
| Context diagram | კონტექსტური დიაგრამა | Context diagram |

### Stakeholders and governance

| Concept | Georgian | English / Russian |
|---|---|---|
| Stakeholder | დაინტერესებული მხარე | Stakeholder / заинтересованная сторона |
| Sponsor | სპონსორი | Sponsor / спонсор |
| Process owner | პროცესის მფლობელი | Process owner / владелец процесса |
| Key user | ძირითადი მომხმარებელი | Key user / ключевой пользователь |
| Steering committee | მმართველი კომიტეტი | Steering committee / управляющий комитет |
| Decision log | გადაწყვეტილებების ჟურნალი | Decision log |
| Sign-off | შეთანხმება, ხელმოწერა | Sign-off / лист согласования |
| Escalation | ესკალაცია | Escalation |
| Risk register | რისკების რეესტრი | Risk register / реестр рисков |

### 1C / ERP implementation

| Concept | Georgian | Russian (canonical) |
|---|---|---|
| Pre-project survey | წინასაპროექტო კვლევა | Предпроектное обследование |
| Survey report | კვლევის ანგარიში | Отчёт об обследовании |
| Standard configuration | ტიპური კონფიგურაცია | Типовая конфигурация |
| Customization / modification | ტიპური კონფიგურაციის მოდიფიცირება | Доработка |
| Configuration extension | კონფიგურაციის გაფართოება | Расширение конфигурации (.cfe) |
| Support mode | მხარდაჭერის რეჟიმი | Режим поддержки |
| Removed from support | მხარდაჭერიდან მოხსნილი | Снят с поддержки |
| Gap | განსხვავება, შეუსაბამობა | GAP |
| Fit-gap analysis | fit-gap ანალიზი | FIT/GAP-анализ |
| Design decision document | საპროექტო გადაწყვეტა | Проектное решение (ПР) |
| Development task | დავალება დეველოპერისთვის | Постановка задачи / ЧТЗ / ЗНР |
| Test program and method | ტესტირების პროგრამა და მეთოდიკა | ПМИ |
| Acceptance testing | მიღების ტესტირება | Приёмочные испытания |
| Control example | საკონტროლო მაგალითი | Контрольный пример |
| Trial operation | საცდელი ექსპლუატაცია | Опытная эксплуатация (ОЭ) |
| Pilot / parallel operation | საცდელ-სამრეწველო ექსპლუატაცია | Опытно-промышленная эксплуатация (ОПЭ) |
| Production operation | სამრეწველო ექსპლუატაცია | Промышленная эксплуатация (ПЭ) |
| Go-live | ექსპლუატაციაში გაშვება | Ввод в эксплуатацию |
| Cutover | გადართვა | Переход / cutover |
| Master data | ძირითადი / საცნობარო მონაცემები (ნორმატიულ-საცნობარო ინფორმაცია) | НСИ |
| Opening balances | საწყისი ნაშთები | Начальные остатки |
| Data migration | მონაცემების გადატანა | Перенос данных / миграция |
| Reconciliation | შეჯერება, შედარება | Сверка |
| Period close | პერიოდის დახურვა | Закрытие периода |
| Catalog | ცნობარი | Справочник |
| Document | დოკუმენტი | Документ |
| Information register | ცნობების რეგისტრი | Регистр сведений |
| Accumulation register | დაგროვების რეგისტრი | Регистр накопления |
| Attribute | რეკვიზიტი | Реквизит |
| Tabular section | ცხრილოვანი ნაწილი | Табличная часть |
| Posting | გატარება | Проведение |
| Register movement | მოძრაობა რეგისტრში | Движение по регистру |
| Printed form | ბეჭდვითი ფორმა | Печатная форма |
| Access rights / RLS | წვდომის უფლებები / ჩანაწერის დონის შეზღუდვა | Права доступа / RLS |
| Data exchange | მონაცემთა გაცვლა | Обмен данными |

## Phrasing notes

A few constructions that keep Georgian analyst prose readable:

- Prefer the plain verbal noun to a heavy nominal chain: `მოთხოვნების შეგროვება` rather than a stacked genitive string of four nouns.
- For a requirement statement, Georgian has no natural equivalent of the binding "shall". Use `სისტემამ უნდა ...` consistently for a binding requirement and reserve `სასურველია` / `რეკომენდებულია` for non-binding ones — and say in the glossary section of the document which is which, exactly as you would define shall/should in an English specification.
- For conditional requirements, the EARS shapes translate cleanly, but the connector has to carry a finite clause or the sentence reads as unfinished — and `სანამ` alone reads as "until", which inverts a state-driven requirement. Use: `როდესაც <მოვლენა ხდება>, სისტემამ უნდა ...` (event-driven), `სანამ <მდგომარეობა> ძალაშია, სისტემამ უნდა ...` or, less ambiguously, `<მდგომარეობის> პერიოდში სისტემამ უნდა ...` (state-driven), `თუ <არასასურველი პირობა დგება>, მაშინ სისტემამ უნდა ...` (unwanted behaviour). Keeping these three shapes consistent across a document does more for clarity than any amount of polishing.
- Avoid the vague adverbs that are as unverifiable in Georgian as in English: `სწრაფად`, `მოსახერხებლად`, `საჭიროებისამებრ`, `და ა.შ.`. Each is a defect in a requirement.
- When a number is unknown, write `[დასაზუსტებელია]` rather than a plausible placeholder. A placeholder becomes a requirement the moment somebody signs the document.
