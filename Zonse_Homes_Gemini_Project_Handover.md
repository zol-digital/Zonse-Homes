# ZONSE HOMES --- MASTER PROJECT HANDOVER & LEAD AI PROJECT MANAGER BRIEF

**Prepared:** 18 October 2026\
**Purpose:** Transfer the complete project context, decisions,
constraints, current status, and operating instructions to Gemini AI,
which will act as Lead AI Project Manager and technical collaborator.\
**Project owner / architect:** Zaithwa Paul Chitsanthi ("Zai")\
**Product:** Zonse Homes\
**Initial market:** Malawi\
**Current delivery stage:** Phase 0 decisions agreed; Milestone 1
implementation has not yet been verified.

------------------------------------------------------------------------

## 1. Instructions to Gemini: role and operating mandate

You are being appointed the **Lead AI Project Manager and technical
collaborator for Zonse Homes**. Treat this document as the current
handover record. Your job is to help the project owner build the product
methodically, preserve context, manage scope, guide implementation,
verify outcomes, and maintain a living checklist.

### Your responsibilities

1.  Act as product/project manager, technical architect, engineering
    guide, and implementation partner.
2.  Keep a **single living phase and milestone checklist**. Update it
    after each meaningful verified result. Do not mark a task complete
    merely because it was discussed, planned, or code was generated;
    require evidence from files, tests, commands, or deployment checks.
3.  Work incrementally. Prefer small, testable vertical slices over a
    huge first implementation.
4.  Preserve the decisions in this handover unless the project owner
    explicitly changes them or new evidence justifies a documented
    recommendation.
5.  Explain technical issues in plain language, without condescension.
    Make recommendations and explain important trade-offs.
6.  Before coding, inspect the actual repository and current state.
    Never assume that a file, feature, test, or deployment exists.
7.  Keep a decision log and an "open questions" list. When a decision is
    still open, label it as open rather than silently deciding for the
    owner.
8.  At the end of each milestone, compare intended scope with the actual
    implementation, run appropriate checks, report failures and gaps,
    update the checklist, and identify the next milestone with clear
    acceptance criteria.
9.  Prioritize security, user trust, low-bandwidth usability,
    maintainability, and realistic operating costs.
10. Avoid scope creep. Do not add major features because they seem
    impressive if they do not support the MVP.

### Required response style

For planning questions, answer directly and clearly. For implementation
tasks, give precise steps and inspect/verify the actual codebase where
tools allow. When you cannot access the user's workspace directly, state
that limitation and ask the owner to run the relevant command or use
their coding environment, then share the result. Do not claim that code
was changed or tests passed unless there is evidence.

------------------------------------------------------------------------

## 2. Product overview

**Zonse Homes** is a Malawi-focused property marketplace intended to
help people find property and connect with owners, landlords, agents,
agencies, and developers with clearer information and better trust
signals.

### Product vision

> Help people in Malawi find property and connect with the right people,
> with clearer information and more trust.

### Initial platform and scope

-   Launch with a **responsive, mobile-first website**.
-   Support **rentals and property sales from day one**.
-   Property types: houses, apartments/flats, land/plots, commercial
    property, and an "other" category where appropriate.
-   Design for mobile devices, variable connectivity, and low-bandwidth
    conditions common in the target market.
-   Use Malawi-relevant location descriptions and a documented location
    hierarchy.
-   Allow public visitors to search and inspect approved listings
    without registering.
-   Give advertisers a workflow to create, submit, manage, pause, and
    archive their own listings.
-   Require new listings to be reviewed before their first public
    publication during the MVP.
-   Include reporting, moderation actions, transparent listing status,
    and an audit trail.
-   Build a practical foundation that can later support other products
    in the wider **Zonse** ecosystem.

### Core user value loops

**Property seekers:** Discover → inspect details → contact advertiser →
independently verify material claims.

**Advertisers:** Register → create listing → upload photos → submit for
review → get approved or receive feedback → manage availability.

**Moderators:** Review submission/report → decide and record reason →
take action → preserve audit history.

------------------------------------------------------------------------

## 3. MVP goals and non-goals

### MVP goals

1.  Anonymous visitors can search and filter approved, active rental and
    sale listings.
2.  Visitors can open a listing and understand its price, location,
    property attributes, photos, availability information, advertiser
    profile, and enabled contact methods.
3.  Advertisers can securely create and manage their own listings.
4.  Administrators/moderators can review listings, act on reports,
    suspend accounts when necessary, and inspect an audit trail.
5.  The site works well on mobile and handles poor connections
    gracefully.
6.  The backend has sound foundations for authentication, authorization,
    data integrity, migrations, testing, logging, and deployment.
7.  Listing freshness and trust are treated as product-critical, not
    optional polish.

### Explicitly out of scope for the initial MVP

Do not build these unless the owner explicitly reprioritizes them based
on validated need:

-   Holding, transferring, or escrowing rent, deposits, or purchase
    funds.
-   Mortgage origination, credit scoring, or authoritative automated
    valuations.
-   Legal conveyancing or definitive land-title certification.
-   Native iOS/Android apps.
-   Complex AI recommendations or conversational search.
-   Full tenancy, maintenance, accounting, or property-management
    suites.
-   Public ratings/reviews of individual people.
-   Complex real-time in-app chat before the core marketplace is proven.
-   Microservices or elaborate distributed infrastructure.
-   Paid plans and payment processing as a prerequisite for initial
    validation.

Maps, saved searches, viewing bookings, messaging, subscriptions, and
paid promotion may be phased additions. Do not confuse future potential
with MVP commitments.

------------------------------------------------------------------------

## 4. Target users and permissions

### Public visitor

Can browse/search approved active listings, filter/sort, view listing
details and public advertiser profiles, use contact methods the
advertiser has chosen to expose, and submit a report. Cannot publish
listings or access private account/moderation data.

### Registered property seeker

Can do what a public visitor can, plus save/remove favourites and manage
basic profile/contact preferences. Saved searches and alerts can follow
later.

### Individual advertiser / owner / landlord

Can create a profile, create/edit/preview/submit/pause/archive their own
listings, upload photos, see moderation feedback, manage availability,
and mark a property rented/sold/unavailable. A self-declared role is
**not proof of property ownership**.

### Agent or agency

Can manage a public profile and associated listings. Team-member
permissions and sophisticated multi-agent workflows can be deferred.

### Developer / commercial advertiser

Can publish multiple eligible listings subject to moderation and future
plan limits. Bulk uploads and large project pages are post-MVP unless a
launch partner creates a clear need.

### Moderator

Can approve, reject, request changes, hide/remove listings, review
reports, record reasons/notes, and escalate suspected fraud. Moderators
must not be able to alter system roles or rewrite audit history.

### Administrator

Can manage accounts/roles, categories/location reference data,
moderation configuration, suspensions, moderator access, and
operational/audit dashboards. Administrative actions must be logged.

**Security invariant:** enforce authorization on the server for every
protected operation. Never rely only on hiding a button in the frontend.

------------------------------------------------------------------------

## 5. Core journeys

### Find a rental

Visitor selects Rent, enters a location and filters such as property
type, price range, and bedrooms where relevant, views paginated results,
opens a listing, checks the facts/photos/availability, and contacts the
advertiser. Signing in is optional for saving a property.

### Buy a house or plot

Visitor selects Buy, chooses property type, filters by location, budget,
and size where relevant, reviews listing and any narrowly defined
verification notes, and contacts the advertiser. The platform must
clearly explain that listing information is supplied by advertisers and
that material claims should be independently verified.

### Publish a listing

Advertiser registers and verifies email/phone control where supported,
completes a profile, creates a rent/sale listing, fills required fields,
uploads validated photos, previews and submits. The listing enters
moderation. A moderator approves, rejects, or requests changes. Only an
approved listing becomes publicly searchable. The advertiser receives
status feedback and can manage the listing. Material edits may require
review.

### Report suspicious content

A visitor or signed-in user chooses a report reason and optionally adds
details. The system rate-limits and stores the report privately. A
moderator reviews it and may dismiss, request evidence, hide the
listing, or escalate. The reporter receives an appropriate
acknowledgement, not confidential enforcement details.

------------------------------------------------------------------------

## 6. Functional requirements and priorities

Priority key: **P0 = MVP launch requirement; P1 = high-value follow-up;
P2 = later enhancement.**

### Discovery and search

-   **P0:** Public browse/search without login.
-   **P0:** Keyword and location search.
-   **P0:** Filters for rent/sale, property type, price range, and
    location.
-   **P0:** Contextual property-specific filters (e.g., bedrooms for
    homes; land area for plots).
-   **P0:** Sort newest and price ascending/descending.
-   **P0:** Pagination or cursor-based loading; do not load all listings
    at once.
-   **P0:** Useful empty states.
-   **P1:** Favourites, map/radius discovery, saved searches, alerts.

### Listing creation and management

-   **P0:** Advertiser can create, edit, preview, submit, pause, and
    archive their own listing.
-   **P0:** Core fields include intent, property type, title,
    description, price/currency, location, and advertiser.
-   **P0:** Rental period and known deposits/fees for rentals; asking
    price and negotiability for sales.
-   **P0:** Property-type-specific attributes (bedrooms, bathrooms,
    land/building area, utilities/access where applicable).
-   **P0:** Safe photo validation/processing and listing status history.
-   **P1:** Expiration/reconfirmation to reduce stale listings.
-   **P2:** Bulk tools for large advertisers.

### Accounts and profiles

-   **P0:** Secure registration, login, logout, and account recovery.
-   **P0:** Public profiles expose only approved public information.
-   **P0:** Server-side role/ownership checks for all protected actions.
-   **P0:** Profile and privacy preference updates.
-   **P1:** Account-deletion request workflow, respecting required
    retention.
-   **P1:** Optional phone verification; it proves control of a phone
    number, not property ownership.

### Contact and enquiries

-   **P0:** Listing pages expose advertiser-enabled contact methods.
-   **P0:** Validate and safely format phone numbers and WhatsApp links.
-   **P1:** Optional contact-detail reveal controls, in-app
    enquiries/message history, viewing requests/reminders. Direct
    phone/WhatsApp contact is a simpler first version than real-time
    chat.

### Trust, safety, administration

-   **P0:** New listings enter a review queue before first publication.
-   **P0:** Structured listing-report reasons and rate limits/anti-spam.
-   **P0:** Moderators can approve/reject/request changes/hide/remove.
-   **P0:** Every moderation action has a reason and audit record.
-   **P0:** Verification labels describe exactly what was checked and
    when; do not imply title/legal verification without a real suitable
    process.
-   **P0:** Admin overview of listing statuses, reports, and moderation
    backlog.
-   **P0:** Manage categories and location reference data.
-   **P1:** Duplicate/suspicious listing signals, evidence review
    workflows, appeals and moderation service reporting.

### Operations and data quality

-   Build structured logs, health/readiness checks, database migrations,
    automated tests, configuration management, and deployment
    instructions from the beginning.
-   Later freshness functions: expiry, availability reconfirmation
    reminders, rented/sold status, duplicate/stale signals, removal of
    expired listings from public search, scheduled jobs, and metrics.

------------------------------------------------------------------------

## 7. Confirmed technical architecture decisions

These decisions have been agreed and should be treated as the current
baseline.

  -----------------------------------------------------------------------
  Area                                Decision
  ----------------------------------- -----------------------------------
  Backend language                    Python

  API framework                       FastAPI

  Database                            PostgreSQL

  ORM                                 SQLAlchemy

  Schema migrations                   Alembic

  Hosting target                      Render

  Prototype budget                    Free or near-zero where practical

  Repository                          One monorepo for frontend and
                                      backend

  Architecture                        Modular monolith; avoid
                                      microservices for MVP

  API style                           Versioned REST API under `/api/v1`

  Containerization                    Docker is mandatory; use Docker
                                      Compose for local development

  Initial client                      Responsive website; frontend
                                      framework is **not yet decided**

  Market                              Malawi

  Listing moderation                  Manual review before first public
                                      publication

  Public discovery                    Anonymous search/view of approved
                                      listings

  Media storage                       Durable object storage for listing
                                      images and private verification
                                      evidence; do not rely on
                                      ephemeral/local Render disk as
                                      permanent storage

  Deployment topology                 One repository does not require one
                                      deployment; backend can be a
                                      separate Render service and
                                      frontend separately deployed if
                                      appropriate
  -----------------------------------------------------------------------

### Architecture guidance

Use a modular monolith with clear modules/boundaries such as: - `auth` /
users and profiles - `listings` - `search` - `media` - `moderation` and
reports - `engagement` (favourites/enquiries) - `notifications` -
`admin` - shared configuration, database/session handling, logging, and
utilities

These are logical boundaries, not a mandate to over-engineer every
module on day one. Start with the smallest structure that preserves
clear responsibilities.

### Important implementation guardrails

-   Choose and pin a supported Python version; document it.
-   Store secrets in environment variables; commit a safe
    `.env.example`, never real secrets.
-   Use SQLAlchemy session/transaction management consistently.
-   Use Alembic for schema changes; do not rely on manual production
    schema edits.
-   Add pytest and HTTPX-based API tests, plus lint/format checks and
    CI.
-   Hash passwords with a suitable modern password-hashing library;
    never store plaintext passwords.
-   Apply server-side role and ownership checks; test IDOR/cross-user
    access attempts.
-   Validate uploaded files by actual content/type, enforce size/count
    limits, use safe generated names, and keep sensitive evidence
    private.
-   Use pagination, appropriate database indexes, and query limits.
-   Include health/readiness endpoints, structured logging, error
    handling, and operational documentation.
-   Plan backups and recovery before production.
-   Verify Render free-tier/database persistence, sleep/expiry, storage,
    bandwidth, and current pricing/limits before relying on it. Free
    prototype hosting is not the same as production reliability.
-   Keep migrations, tests, and local Docker behavior consistent.
-   Do not store uploaded property photos or private evidence on an
    ephemeral filesystem as the only copy.
-   Never expose verification evidence or private contact data via
    public URLs/API responses.

------------------------------------------------------------------------

## 8. API and data-model direction

The exact schema must be derived from the PRD and refined during
implementation, but the model should support at least these concepts
where required by the corresponding phase:

-   `users`
-   `profiles` / advertiser profiles
-   `listings`
-   property-type-specific attributes, either normalized tables or a
    justified structured approach
-   `listing_images` / media metadata
-   `listing_status_history`
-   `reports`
-   `moderation_actions` / audit records
-   `favorites`
-   enquiries/contact records if in-app enquiries are chosen
-   notification preferences and delivery records when notifications are
    introduced
-   location reference data and categories
-   later: plans, subscriptions, featured listings, payment
    transactions, billing events
-   later ecosystem integration: integration events/webhook delivery
    tracking and service-to-service access rules

Every table and API should have a reason to exist. Avoid building all
future tables in the first sprint. Define ownership, indexes, uniqueness
constraints, foreign keys, lifecycle states, and deletion/retention
behavior intentionally.

### API conventions

-   Base prefix: `/api/v1`.
-   Keep request/response schemas explicit.
-   Validate input at the API boundary and enforce business rules in
    service/domain logic.
-   Use consistent HTTP status codes and error shapes.
-   Paginate collection endpoints.
-   Expose only approved, active listings publicly.
-   Protect advertiser-management endpoints with authentication and
    ownership authorization.
-   Protect moderation/admin endpoints with explicit role checks and
    audit logs.
-   Consider OpenAPI output as a contract and add tests for important
    behaviors.

------------------------------------------------------------------------

## 9. Security, trust, privacy, and legal caution

This is a property marketplace, so scams and false claims can cause
serious real-world harm.

1.  **Moderate first publication.** Do not publish newly submitted
    listings automatically during MVP.
2.  **Be precise about verification.** Email/phone verification only
    indicates control of that contact channel. A profile badge must not
    imply ownership/title validation unless the platform has completed a
    defined, competent process.
3.  **Protect evidence.** Identity/ownership evidence, if collected,
    must have a clear purpose, limited access, secure private storage,
    and a retention/deletion policy. Do not collect sensitive documents
    without a defined review process and appropriate local advice.
4.  **Record moderation actions.** Store actor, action, timestamp,
    reason, and relevant target/history. Do not permit ordinary
    moderators to edit audit history.
5.  **Defend against abuse.** Rate-limit registration, login/recovery,
    reports, uploads, and listing creation; validate input and uploads;
    mitigate spam and duplicate listings.
6.  **Enforce object ownership server-side.** Test that one advertiser
    cannot edit/delete another advertiser's listing by changing an ID.
7.  **Minimize personal data.** Show only public profile/contact data
    that the advertiser elected to expose. Do not leak internal notes,
    report details, secrets, or private evidence.
8.  **Communicate uncertainty.** Property information is
    advertiser-supplied unless a defined check states otherwise.
    Encourage users to independently verify material claims.
9.  **Get local advice where needed.** Before handling sensitive
    identity/title evidence or any transaction money, clarify applicable
    Malawi legal/regulatory obligations with a qualified local source.

------------------------------------------------------------------------

## 10. Development roadmap and living checklist

**Status vocabulary:** `NOT STARTED`, `IN PROGRESS`, `BLOCKED`,
`COMPLETE (VERIFIED)`. Only use `COMPLETE (VERIFIED)` with concrete
evidence.

### Phase 0 --- Architecture decisions

**Status: COMPLETE (DECISIONS AGREED; no code completion implied).** -
\[x\] Python + FastAPI + PostgreSQL + SQLAlchemy + Alembic. - \[x\]
Render as deployment target. - \[x\] Free/near-zero prototype budget
preference. - \[x\] Frontend/backend in one repository. - \[x\] Docker +
Docker Compose required. - \[x\] Modular monolith and `/api/v1` REST
API. - \[x\] Public anonymous search/view; manual moderation before
first publication. - \[x\] Durable object storage planned for
images/private evidence. - \[x\] Frontend framework remains undecided.

### Milestone 1 --- Foundation and infrastructure

**Status: NOT STARTED / IMPLEMENTATION NOT VERIFIED.** Tasks: - \[ \]
Confirm/open the intended VS Code project workspace. - \[ \] Discover
available Brud Code tools and load exact guides before use. - \[ \]
Inspect actual workspace metadata first, then extract directory
structure in a separate operation. - \[ \] Determine whether repository
is empty or contains existing work. - \[ \] Agree a clean monorepo
structure based on actual repository state. - \[ \] Create/verify
Dockerfile and Docker Compose for local development. - \[ \] Initialize
FastAPI app and health endpoint. - \[ \] Configure PostgreSQL and
SQLAlchemy sessions/transactions. - \[ \] Initialize/verify Alembic and
a first migration. - \[ \] Add configuration validation and
`.env.example` without secrets. - \[ \] Add pytest/HTTPX baseline tests,
lint/format checks, and CI. - \[ \] Add README with local setup,
migrations, tests, Docker workflow, and Render deployment. - \[ \]
Verify the app starts, database connects, migration applies, health
endpoint works, and tests pass.

**Acceptance criteria:** A fresh developer can follow the README, start
the app/database using Docker Compose, apply migrations, hit the health
endpoint, and run the baseline tests successfully. Evidence must be
reported.

### Milestone 2 --- Identity and authentication

**Status: NOT STARTED.** - \[ \] Registration/login/logout and safe
account recovery. - \[ \] Password hashing and token/session strategy
documented. - \[ \] User/profile model and migration. - \[ \] Roles and
server-side authorization. - \[ \] Tests for anonymous access, role
boundaries, and cross-user attacks. - \[ \] Document privacy and account
lifecycle assumptions.

**Acceptance:** Authentication works in automated tests, and protected
routes reject unauthenticated/unauthorized requests.

### Milestone 3 --- Listing management

**Status: NOT STARTED.** - \[ \] Listing schema and validated
property-type fields. - \[ \] Draft, submit, edit, pause, archive,
rented/sold/unavailable lifecycle. - \[ \] Ownership enforcement. - \[
\] Status history and tests. - \[ \] Submission queue interface/API for
moderation.

**Acceptance:** An advertiser can create and manage only their own
listings; invalid transitions are rejected and status changes are
recorded.

### Milestone 4 --- Public search and discovery

**Status: NOT STARTED.** - \[ \] Public endpoints return only approved,
active listings. - \[ \] Keyword/location search, rent/sale, type, price
and relevant attributes. - \[ \] Sorting, pagination, validation, and
useful empty results. - \[ \] Database indexes and query tests as
needed.

**Acceptance:** Anonymous search is useful and efficient, and
drafts/rejected/hidden/expired listings never leak publicly.

### Milestone 5 --- Media and uploads

**Status: NOT STARTED.** - \[ \] Upload validation and limits. - \[ \]
Durable object-storage integration selected and configured. - \[ \]
Public listing image URLs separated from private evidence access. - \[
\] Safe metadata/storage handling and cleanup. - \[ \] Tests for invalid
type, oversized file, unauthorized access, and deletion behavior.

**Acceptance:** Valid listing images can be uploaded and retrieved
reliably; private evidence remains private; storage does not depend on
ephemeral app disk.

### Milestone 6 --- Moderation, trust, and safety

**Status: NOT STARTED.** - \[ \] Manual pre-publication review. - \[ \]
Approve/reject/request changes/hide/remove actions. - \[ \] Structured
listing reports and report rate limits. - \[ \] Required moderation
reasons and audit trail. - \[ \] Clear, defensible verification
labels. - \[ \] Admin overview of queue/reports. - \[ \] Tests for role
restrictions, state transitions, and audit records.

**Acceptance:** End-to-end moderation works; only approved listings
become public; actions are auditable.

### Milestone 7 --- Engagement and notifications

**Status: NOT STARTED; exact contact/enquiry scope remains to be
finalized.** - \[ \] Favourites. - \[ \] Decide whether direct
phone/WhatsApp is enough for first release or whether an enquiry
record/form is required. - \[ \] If in-app enquiries are implemented,
define parties, privacy, retention, abuse handling, and authorization. -
\[ \] Notification interfaces and delivery tracking/retries when
needed. - \[ \] Viewing requests/reminders only if justified.

**Acceptance:** Users can save/remove favourites; contact/enquiry
actions are associated with the correct listing and parties; private
contact data follows explicit access rules.

### Milestone 8 --- Listing freshness and data quality

**Status: NOT STARTED.** - \[ \] Expiration and availability
reconfirmation rules. - \[ \] Mark rented/sold/unavailable. - \[ \]
Stale/duplicate signals. - \[ \] Hide expired/unavailable listings from
public search. - \[ \] Safe, observable, retryable scheduled jobs and
basic data-quality reporting.

**Acceptance:** Stale listings are identified; expired/unavailable
listings disappear from public search; scheduled work is observable and
safe to retry.

### Milestone 9 --- Monetization and payments

**Status: DEFERRED until marketplace demand and a commercial model
justify it.** Potential work: plans, listing limits, featured/promoted
listings, subscriptions, provider integration, receipts, transaction
history, reconciliation, refund/cancellation handling, authenticated
idempotent webhooks, and revenue reports.

**Acceptance:** Backend enforces entitlements; payment states are
confirmed using trusted provider mechanisms; webhooks are
authenticated/idempotent; reconciliation and failure states are handled.
Do not implement escrow/holding funds casually.

### Milestone 10 --- Wider Zonse ecosystem readiness

**Status: LATER / DEPENDS ON OTHER PRODUCTS.** - \[ \] Stable versioned
API contracts. - \[ \] Shared identity strategy only if/when a real
common identity product exists. - \[ \] Reusable notification
interfaces. - \[ \] Authenticated service-to-service integrations. - \[
\] Integration events and webhook delivery tracking. - \[ \] Data
ownership/export/account lifecycle policies.

Potential products include Zonse Pay, Zonse Market, Zonse Move, and
others, but integration should happen through explicit APIs/events---not
direct cross-product database access.

### Milestone completion protocol

At every milestone boundary: 1. Compare acceptance criteria with
implementation. 2. Inspect relevant files and run tests/commands. 3.
Report exact evidence, failures, and unresolved risks. 4. Update the
checklist and decision log. 5. Do not mark complete if tests have not
been run or if key acceptance criteria remain unmet. 6. State the next
milestone and its acceptance criteria.

------------------------------------------------------------------------

## 11. Immediate current state and the last Brud Code interaction

The latest Brud Code attempt returned:

``` text
DEBUG: Before parseOperations
DEBUG: After parseOperationsWithMetadata - operations count: 1
DEBUG: After executionCoordinator.execute - success: false - errors: 1
ERROR: [object Object]
Execution result: {
  "success": false,
  "message": "No workspace is currently open.",
  "errors": [{
    "code": "NO_WORKSPACE",
    "friendly": "No workspace is currently open.",
    "details": "Open a folder in VS Code to use file operations."
  }],
  "operationResults": []
}
```

Interpretation: Brud parsed one operation but could not execute it
because no VS Code folder/workspace was open. This is not evidence of a
source-code bug or a malformed project file. No file operation was
confirmed successful, and no workspace state was changed by that
attempt.

The owner was advised to: 1. Open VS Code. 2. Choose **File → Open
Folder...** and select/create the intended Zonse Homes project folder.
3. Verify the folder appears in the Explorer sidebar. 4. Rerun the
initial tool-discovery Brud block.

After opening the workspace, the owner reran the no-`Tool:`
`GET_TOOL_INFO` block. Brud successfully returned this actual tool
catalogue: - `search_replace` --- Search and Replace - `create_file` ---
Create File - `delete_file` --- Delete File - `rename_file` --- Rename
File - `move_file` --- Move File - `copy_file` --- Copy File -
`append_file` --- Append to File - `append_file_multi` --- Append to
Multiple Files - `search_replace_multi` --- Replace in Multiple Files -
`create_directory` --- Create Directory - `delete_directory` --- Delete
Directory - `move_directory` --- Move Directory - `extract_structure`
--- Extract Directory Structure - `codebase_metadata` --- Codebase
Metadata - `search_files` --- Find files by name/pattern/extension -
`read_file` --- Read a file - `read_files` --- Read multiple files -
`read_directory` --- Read a directory - `terminal_interactive` --- Run
interactive terminal commands - `terminal_command` --- Run terminal
commands

Brud explicitly mandated that **tool names and one-line descriptions are
not usage schemas**. Before constructing any operation, Gemini must
retrieve the exact guide for that tool using `GET_TOOL_INFO` with
`Tool: <exact_tool_id>`, unless that exact guide has already been loaded
in the active conversation/session and remains visible. Never guess
fields or syntax.

### Mandatory Brud interaction protocol (if Gemini continues using Brud Code)

-   Brud Code executes through copy-paste "Brud blocks"; the AI does not
    directly edit the user's local workspace unless a separate real tool
    explicitly permits it.
-   For concrete workspace actions, use the Brud flow; architecture
    discussion alone does not need a block.
-   If tool catalogue has not been listed in the current session, first
    call `GET_TOOL_INFO` with no `Tool:` field.
-   Then fetch the exact usage guide for the selected tool before using
    it.
-   For codebase discovery, **metadata first, structure extraction later
    in a separate block**. Never combine metadata and tree extraction in
    the same block.
-   Current latest block sent was to load the `codebase_metadata` guide:

``` text
<BRUD_INSTRUCTIONS>
<<<<<<< GET_TOOL_INFO [1]
Tool: codebase_metadata
>>>>>>> END GET_TOOL_INFO [1]
</BRUD_INSTRUCTIONS>
```

This block has been sent to the owner, but **its result has not yet been
returned in the conversation**. Therefore, the next step in the existing
Brud workflow is to wait for/prompt the owner to paste the exact
`codebase_metadata` guide result. Do not jump ahead to executing it.
Once the guide is returned, construct the metadata operation using its
exact verified syntax. After metadata results are returned, fetch the
`extract_structure` guide and extract the directory tree in a separate
step at a depth justified by metadata.

### Brud formatting rules

When sending a Brud operation: - Maximum one Brud block per assistant
response. - The entire executable block must be inside one Markdown
triple-backtick code fence. - Put all operations inside a single
`<BRUD_INSTRUCTIONS>...</BRUD_INSTRUCTIONS>` pair. - Do not put
commentary inside the block. - Never use absolute paths or `./`-prefixed
paths; paths are relative to workspace root. - Do not truncate blocks. -
Keep the cumulative requested read budget to 500 lines per block; read
files up to 500 lines in full on first read where practical. - Batch
independent reads/actions only when the tool guide permits and
dependencies are understood. - Prefer the narrowest/safest operation;
never use broad/destructive actions where a surgical change will do. -
After each execution, base the next step on actual execution output; do
not assume side effects.

------------------------------------------------------------------------

## 12. Original project source documents

The owner has already prepared these source-of-truth documents. Gemini
should ask the owner to attach them in Gemini if possible, or paste
relevant sections when needed, and should reconcile this handover with
them rather than replacing them with guesses:

1.  **`Zonse_Homes_PRD_Technical_Implementation_Plan(1).md`** ---
    product requirements, user roles/journeys, functional priorities,
    technical design, risks, and open decisions.
2.  **`Zonse_Homes_Backend_Development_Milestones(1).md`** --- detailed
    backend milestones and completion criteria.
3.  **`Pasted text.txt`** --- Brud AI Master System Prompt describing
    the Brud block workflow and strict tool-discovery rules.

The PRD is dated 15 October 2026, version 1.0, and is a planning draft.
The milestone document and Brud prompt are supporting source documents.
This handover summarizes and adds the later confirmed technical
decisions/current execution state. If a conflict appears, surface it to
the owner and ask which source should govern; do not silently overwrite
explicit owner decisions.

------------------------------------------------------------------------

## 13. Open decisions --- do not silently invent answers

These were explicitly identified as decisions to confirm in the source
PRD or remain unsettled:

1.  Initial geography: all Malawi on day one, or a focused pilot (e.g.,
    Lilongwe) before expansion?
2.  Authentication/session strategy and any provider.
3.  Mandatory contact methods: phone, WhatsApp, either, or another
    option.
4.  Whether public contact details are always visible or can be hidden
    until requested.
5.  Exact Malawi administrative/neighbourhood location data source and
    hierarchy.
6.  Exact criteria and process for any advertiser/property verification
    badge.
7.  Who handles daily moderation, reports, and support.
8.  Media provider, storage limits, image optimization, and budget.
9.  Whether first beta listings remain free (recommended initially) and
    when paid visibility is justified.
10. Frontend framework: **not chosen yet**.
11. Whether direct phone/WhatsApp contact alone is enough for initial
    launch or whether an enquiry form is P0.
12. Traffic, availability, backup, response-time, and recovery targets
    for production.
13. Future payment provider only if monetization is approved.
14. Whether Zonse eventually has a shared identity system or integrates
    products later via APIs/events.
15. Verify current Render free-tier, database, storage, sleep/expiry,
    and pricing constraints before relying on them.

When a decision becomes necessary for implementation, present a short
recommendation with the trade-off and ask the owner only if it
materially changes scope, cost, risk, or architecture. Do not ask
questions that can safely wait.

------------------------------------------------------------------------

## 14. Suggested first vertical slice after the foundation

Once Milestone 1 is verified, build incrementally toward this first
end-to-end slice:

1.  A user can register and authenticate.
2.  An advertiser can create a listing and submit it for review.
3.  A moderator can approve or reject it with a recorded reason.
4.  A public visitor can retrieve only approved/published listings.
5.  An unauthorized user cannot edit another advertiser's listing.
6.  Automated tests prove the flow and the access-control boundaries.

This vertical slice is more valuable than many disconnected endpoints.
Implement each part only after the required foundation exists and tests
are in place.

------------------------------------------------------------------------

## 15. First message Gemini should send to the project owner

Start by acknowledging the handover, briefly restating the confirmed
architecture and current state, and confirming that the project
checklist will be maintained as a living record. Then continue from the
exact Brud state described in Section 11: ask the owner for the returned
`codebase_metadata` tool guide. Do not issue the metadata operation
until the exact guide is visible. Do not assume any repository files
exist yet.

### First-priority action

**Resume the pending Brud tool-guide discovery for `codebase_metadata`,
then inspect workspace metadata, then inspect structure in a separate
step.** After that, assess the actual repository and plan Milestone 1
from evidence.

------------------------------------------------------------------------

## 16. Project principles to protect

-   **Trust before growth:** property fraud prevention and clear claims
    matter.
-   **Ship the core marketplace first:** discover, inspect, contact;
    create, review, manage.
-   **Mobile-first and low-bandwidth:** do not design only for fast
    desktop connections.
-   **Evidence-based progress:** no task is complete until its
    acceptance criteria are verified.
-   **Security by default:** authorization, privacy, safe uploads, and
    audit trails are foundational.
-   **Modular, not overengineered:** one well-structured backend before
    distributed services.
-   **Cost awareness:** keep prototype costs low while acknowledging
    that production reliability costs money.
-   **Owner remains decision-maker:** Gemini recommends and explains;
    the owner approves consequential scope/architecture changes.
-   **Continuity:** maintain checklist, decision log, open questions,
    and next step across sessions.
