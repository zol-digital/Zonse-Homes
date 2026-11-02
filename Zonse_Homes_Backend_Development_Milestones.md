# Zonse Homes

## Backend Development Phases & Implementation Milestones

**Document purpose:** Define the backend milestones, core system
components, and completion criteria for building Zonse Homes as part of
the wider Zonse app ecosystem.

------------------------------------------------------------------------

## 1. Recommended Backend Architecture

Build Zonse Homes initially as a **modular monolith**: one backend
application organized into clearly separated modules, backed by one
relational database. This keeps the first release manageable while
allowing the system to scale and separate services later if needed.

### Recommended baseline

-   **API:** REST API, versioned from the beginning (for example,
    `/api/v1`)
-   **Database:** PostgreSQL
-   **Data access:** Prisma or Drizzle ORM, with versioned migrations
-   **Backend organization:** Separate modules for identity, listings,
    search, media, moderation, engagement, notifications, billing, and
    integrations
-   **Media storage:** S3-compatible object storage
-   **Background processing:** Scheduled jobs and a job queue when
    needed
-   **Operations:** Separate development, staging, and production
    environments; structured logs, monitoring, backups, and CI checks

Avoid splitting the backend into microservices at the start. Keep
modules independent in code and avoid direct database access across
future Zonse apps.

------------------------------------------------------------------------

## 2. Backend Development Milestones

## Milestone 1 --- Foundation & Infrastructure

**Goal:** Establish a stable, secure backend foundation before
implementing business features.

### Build

-   Backend project structure and module boundaries
-   Development, staging, and production configuration
-   PostgreSQL connection and migration workflow
-   Environment-variable validation and secrets handling
-   Shared request validation, error handling, and response conventions
-   API versioning, such as `/api/v1`
-   Structured application logging
-   CI pipeline for linting, type checks, and automated tests
-   Health, readiness, and version endpoints
-   Database backup and recovery approach

### Completion criteria

-   The application starts consistently in each environment.
-   Database migrations can be applied to a clean database and an
    existing database.
-   Secrets are not committed to source control.
-   CI runs automatically and blocks broken changes.
-   Health endpoints accurately report application and database
    readiness.

------------------------------------------------------------------------

## Milestone 2 --- Authentication, Users & Permissions

**Goal:** Establish user identity and control what each account is
allowed to do.

### Build

-   Registration, login, logout, and account recovery
-   Secure session or token management
-   User profiles and editable contact details
-   Account status controls: active, suspended, disabled, or deleted
-   Email and phone confirmation flows where supported
-   Role-based access control (RBAC)
-   Permission checks enforced on the server, not just in the interface

### Initial roles

-   Visitor / unauthenticated user
-   Property seeker
-   Owner or landlord
-   Agent or agency
-   Moderator
-   Administrator

A user may need more than one capability. For example, an owner may also
search for properties. Avoid designing roles so rigidly that a person
can only ever perform one kind of activity.

### Suggested endpoints

-   `POST /api/v1/auth/register`
-   `POST /api/v1/auth/login`
-   `POST /api/v1/auth/logout`
-   `POST /api/v1/auth/recovery`
-   `GET /api/v1/me`
-   `PATCH /api/v1/me`
-   `GET /api/v1/profiles/:id`

### Completion criteria

-   Authentication and recovery flows work end to end.
-   Private endpoints reject unauthenticated requests.
-   Users cannot access or change another user's private information
    without permission.
-   Role and permission checks have automated tests, including failure
    cases.

------------------------------------------------------------------------

## Milestone 3 --- Property Data Model & Listing Management

**Goal:** Allow authorized users to create, edit, submit, and manage
property listings.

### Supported listing categories

-   Houses
-   Apartments and flats
-   Plots and land
-   Commercial property
-   Other property types, if required

### Listing intent

-   For rent
-   For sale

### Core listing fields

-   Title and description
-   Property category and transaction intent
-   Price and currency, with MWK supported
-   Whether the price is negotiable
-   Rental period and deposit, when applicable
-   Bedrooms, bathrooms, floor area, and land area, where applicable
-   Amenities and utilities
-   Location
-   Availability
-   Contact or advertiser details, subject to privacy settings
-   Listing media and cover image
-   Creation and update timestamps
-   Moderation history

### Listing lifecycle

Use explicit, validated status transitions rather than allowing
arbitrary status changes.

Suggested statuses: - `draft` - `pending_review` - `published` -
`changes_requested` - `rejected` - `paused` - `rented` - `sold` -
`expired` - `removed` - `archived`

### Suggested endpoints

-   `POST /api/v1/listings`
-   `GET /api/v1/listings/:id`
-   `PATCH /api/v1/listings/:id`
-   `POST /api/v1/listings/:id/submit`
-   `POST /api/v1/listings/:id/pause`
-   `POST /api/v1/listings/:id/mark-rented`
-   `POST /api/v1/listings/:id/mark-sold`
-   `POST /api/v1/listings/:id/archive`

### Completion criteria

-   Authorized advertisers can create and manage their own listings.
-   Required fields and property-specific validation are enforced.
-   A user cannot edit or remove another advertiser's listing.
-   Status changes follow approved transitions and are recorded.
-   Listings are not publicly visible merely because they have been
    created.

------------------------------------------------------------------------

## Milestone 4 --- Location Data & Property Search

**Goal:** Make it easy to discover relevant properties, starting with
Malawi.

### Build

-   Structured location reference data suitable for Malawi
-   Support for regions, districts, cities, towns, neighborhoods, and
    aliases as data becomes available
-   Keyword search
-   Filters for location, category, rent/sale, price range, bedrooms,
    bathrooms, and amenities
-   Sorting by newest and price
-   Pagination
-   Public listing response format that does not expose private fields
-   Database indexes for common search and filtering operations

### Suggested endpoints

-   `GET /api/v1/listings`
-   `GET /api/v1/locations`
-   `GET /api/v1/profiles/:id`

### Public search rules

Only return listings that are published, available, not expired, and not
hidden or removed. Apply authorization and privacy rules before
serializing public responses.

### Completion criteria

-   Search and filters return consistent results.
-   Pagination and sorting work predictably.
-   Search excludes unpublished, expired, and removed listings.
-   Common queries use suitable database indexes and meet agreed
    response-time targets.

------------------------------------------------------------------------

## Milestone 5 --- Property Images & Media

**Goal:** Provide a secure and reliable way to upload and display
property photos.

### Build

-   Authorized media-upload workflow
-   S3-compatible object storage
-   File type, file size, and image-dimension validation
-   Generated storage keys rather than user-supplied paths
-   Image resizing and compression
-   EXIF metadata removal, including embedded GPS information
-   Listing cover image and image ordering
-   Limits on the number and size of images per listing
-   Cleanup of abandoned uploads and unused media
-   Access rules for pending, rejected, and published listings

### Suggested endpoints

-   `POST /api/v1/listings/:id/media`
-   `PATCH /api/v1/listings/:id/media/order`
-   `DELETE /api/v1/listings/:id/media/:mediaId`

### Completion criteria

-   Users can upload only to listings they are authorized to manage.
-   Unsupported or oversized files are rejected.
-   Media cannot be attached to another user's listing without
    permission.
-   Public pages expose only media approved for public display.
-   Abandoned uploads can be identified and safely cleaned up.

------------------------------------------------------------------------

## Milestone 6 --- Moderation, Trust & Safety

**Goal:** Reduce fraudulent, misleading, duplicate, or inappropriate
listings and provide administrators with the tools to respond.

### Build

-   Review queue for submitted listings
-   Approve, reject, request changes, or hide listing actions
-   User reporting for listings and advertisers
-   Report review and resolution workflow
-   Account suspension controls
-   Duplicate-listing signals
-   Verification records and evidence-review status
-   Private moderation notes
-   Audit logs for sensitive actions and administrator changes
-   Rate limits and abuse controls for high-risk endpoints

### Suggested endpoints

-   `POST /api/v1/reports`
-   `GET /api/v1/admin/moderation-queue`
-   `POST /api/v1/admin/listings/:id/approve`
-   `POST /api/v1/admin/listings/:id/request-changes`
-   `POST /api/v1/admin/listings/:id/reject`
-   `POST /api/v1/admin/listings/:id/hide`
-   `GET /api/v1/admin/reports`
-   `POST /api/v1/admin/reports/:id/resolve`

### Be precise about verification

Use explicit labels such as: - Email confirmed - Phone confirmed -
Advertiser identity reviewed - Ownership or authority evidence reviewed

Do not describe a property as fully "verified" unless the product has
defined and completed the checks that justify that claim.

### Completion criteria

-   Submitted listings can be reviewed before publication.
-   Reports can be tracked from submission through resolution.
-   Sensitive moderation actions are permission-controlled and audited.
-   Users cannot alter moderation outcomes or view private moderator
    notes.
-   The system has documented procedures for fraud reports and account
    suspension.

------------------------------------------------------------------------

## Milestone 7 --- Engagement & Notifications

**Goal:** Help property seekers keep track of properties and contact
advertisers.

### Build

-   Favourites or saved properties
-   Enquiry records, if in-app enquiries are included
-   Notification preferences
-   Email, SMS, push, or in-app notification adapters as supported
-   Notifications for listing status changes
-   Saved searches, either in this milestone or a later release

### Suggested endpoints

-   `POST /api/v1/listings/:id/favourite`
-   `DELETE /api/v1/listings/:id/favourite`
-   `GET /api/v1/me/favourites`
-   `POST /api/v1/listings/:id/enquiries`
-   `GET /api/v1/me/notifications`

A direct phone or WhatsApp contact link can be an earlier, simpler
launch option. In-app messaging adds privacy, abuse prevention,
moderation, and retention requirements, so define those before
implementing it.

### Completion criteria

-   Users can save and remove favourites.
-   Enquiries are associated with the correct listing and parties.
-   Notification preferences are respected.
-   Notification failures are logged and can be retried safely.
-   Private contact details are not exposed beyond the intended access
    rules.

------------------------------------------------------------------------

## Milestone 8 --- Listing Freshness & Data Quality

**Goal:** Keep the marketplace accurate so users do not waste time
contacting advertisers about unavailable properties.

### Build

-   Listing expiry rules
-   Reminders to reconfirm availability
-   Tools to mark properties as rented or sold
-   Detection signals for stale or duplicate listings
-   Removal of expired or unavailable listings from public search
-   Data-quality metrics and administrative reporting

### Background jobs

-   Listing expiry checks
-   Availability-reconfirmation reminders
-   Notification delivery retries
-   Abandoned-media cleanup
-   Daily operational metrics

### Completion criteria

-   Expired listings stop appearing in public search.
-   Advertisers can update availability through validated actions.
-   Scheduled jobs are observable and safe to retry.
-   Administrators can identify stale listings and review data-quality
    trends.

------------------------------------------------------------------------

## Milestone 9 --- Monetization & Payments

**Goal:** Add paid visibility or commercial plans when the marketplace
has enough value and demand.

This milestone can be deferred until after the public beta. A free
launch may be useful while supply, trust, and engagement are being
established.

### Possible features

-   Listing plans and listing limits
-   Featured or promoted listings
-   Subscription status and renewal tracking
-   Payment-provider integration
-   Receipts and transaction history
-   Payment reconciliation
-   Refund and cancellation workflows, where applicable
-   Revenue and plan-performance reports

### Suggested data entities

-   `plans`
-   `subscriptions`
-   `featured_listings`
-   `payment_transactions`
-   `billing_events`

### Completion criteria

-   Plan entitlements are enforced by the backend.
-   Payment status is confirmed server-side through the provider's
    trusted mechanisms.
-   Webhooks are authenticated, idempotent, and safely retried.
-   Transactions can be reconciled against provider records.
-   Failed, pending, cancelled, and successful payments are handled
    distinctly.

------------------------------------------------------------------------

## Milestone 10 --- Readiness for the Wider Zonse Ecosystem

**Goal:** Make Zonse Homes interoperable with future Zonse products
without tightly coupling their databases or release schedules.

### Build

-   Stable, versioned API contracts
-   Shared-account integration strategy, if a common Zonse identity
    system is introduced
-   Reusable notification interfaces
-   Service-to-service authentication for approved integrations
-   Integration events and webhook delivery tracking
-   Data-export and account-lifecycle policies
-   Clear ownership of data between products

Potential future integrations may include Zonse Pay, Zonse Market, Zonse
Move, or other Zonse products, depending on what is built.

### Integration principle

Use explicit APIs and events rather than allowing one product to read or
write another product's database directly. For example, Zonse Homes
could emit a `listing.rented` event for an authorized downstream
workflow.

### Completion criteria

-   Integrations have documented contracts and access permissions.
-   Events can be retried without creating duplicate side effects.
-   Each product has a clear owner for its data.
-   Existing API clients are protected from unplanned breaking changes.

------------------------------------------------------------------------

## 3. Core Backend Data Entities

The following is a starting inventory. Exact tables and relationships
should be finalized during schema design.

  ---------------------------------------------------------------------------
  Area                    Suggested entities          Purpose
  ----------------------- --------------------------- -----------------------
  Identity                `users`, `profiles`,        Accounts, profiles,
                          `sessions`, `roles`,        sessions, and access
                          `permissions`               control

  Property catalogue      `listings`,                 Property information,
                          `listing_locations`,        location, and features
                          `categories`, `amenities`   

  Media                   `media_assets`,             Uploaded assets,
                          `listing_media`             ordering, and listing
                                                      associations

  Trust and moderation    `reports`,                  Reviews, reports,
                          `verification_checks`,      verification records,
                          `listing_status_history`,   and accountability
                          `audit_logs`                

  Engagement              `favourites`, `enquiries`,  User activity and
                          `notifications`,            communication
                          `saved_searches`            

  Operations              `locations`,                Location lookup,
                          `location_aliases`,         scheduled work, and
                          `background_jobs`,          product metrics
                          `analytics_events`          

  Commercial              `plans`, `subscriptions`,   Monetization and
                          `featured_listings`,        payment records
                          `payment_transactions`,     
                          `billing_events`            

  Integrations            `integration_events`,       Controlled
                          `webhook_deliveries`,       communication with
                          `service_credentials`       other products
  ---------------------------------------------------------------------------

Use foreign keys, unique constraints, and indexes where appropriate.
Avoid collecting personal data that the product does not need, and
define retention rules for enquiries, logs, and account data.

------------------------------------------------------------------------

## 4. Cross-Cutting Requirements for Every Milestone

Every milestone should meet the following baseline before being
considered complete:

1.  **API behavior:** Features work through documented API contracts,
    not only through frontend mock data.
2.  **Validation:** The backend validates user input and rejects invalid
    state transitions.
3.  **Authorization:** Permissions are checked server-side for every
    protected operation.
4.  **Automated tests:** Include success cases, invalid input,
    unauthorized access, and relevant edge cases.
5.  **Security:** Protect secrets and personal data; use rate limits and
    safe error messages where appropriate.
6.  **Observability:** Log meaningful failures and operational events
    without leaking credentials or sensitive personal data.
7.  **Documentation:** Update endpoint, schema, and operational
    documentation.
8.  **Data integrity:** Use database constraints and transactions where
    needed.
9.  **Recovery:** Consider retries, duplicate requests, and failure
    recovery for background jobs and external integrations.
10. **Privacy:** Return only the information the requesting user is
    allowed to see.

------------------------------------------------------------------------

## 5. Recommended Release Sequence

### Public beta: Milestones 1--6

Deliver the foundation, accounts, listing management, search, media
uploads, and moderation. This is the minimum practical backend for a
moderated property marketplace.

### Engagement and quality release: Milestones 7--8

Add favourites, enquiries or contact flows, notifications, expiry, and
availability reconfirmation.

### Commercial release: Milestone 9

Introduce paid plans or promoted listings when there is sufficient
marketplace activity and a clear commercial model.

### Ecosystem expansion: Milestone 10

Add integrations only when other Zonse products and their use cases are
defined.

------------------------------------------------------------------------

## 6. Suggested First Implementation Sprint

Start with a small vertical slice rather than attempting every module at
once.

1.  Create the backend project, environment configuration, PostgreSQL
    database, migrations, and CI checks.
2.  Implement user registration/login and a minimal profile endpoint.
3.  Create the initial listing schema and authorization rules.
4.  Implement listing creation, editing, and submission for review.
5.  Add a minimal moderation action to approve or reject a listing.
6.  Implement a public endpoint that returns only approved, published
    listings.
7.  Add automated tests for the full flow, including attempts to edit
    another user's listing.
8.  Document how to run the backend locally and how to apply migrations.

**First vertical-slice success condition:** An advertiser can create an
account, submit a listing, a moderator can approve it, and a visitor can
retrieve the published listing through the public API---while
unauthorized access is rejected.

------------------------------------------------------------------------

## 7. Key Decisions to Confirm Before Production

-   Which authentication provider or session strategy will be used?
-   Will enquiries happen through phone/WhatsApp links, an in-app form,
    or messaging?
-   Will every listing require moderation before publication?
-   Which Malawi location hierarchy and source data will be used?
-   What image limits and storage budget are acceptable?
-   What exact checks justify advertiser or property verification
    labels?
-   Which payment provider will be supported if monetization is
    introduced?
-   Will Zonse use one shared identity system across products, or will
    integration come later?
-   What are the initial traffic, availability, backup, and
    response-time targets?

These decisions can be made incrementally, but they should be documented
before the related feature reaches production.
