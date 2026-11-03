# Zonse Homes

## Product Requirements Document (PRD) and Technical Implementation Plan

**Version:** 1.0\
**Date:** 15 October 2026\
**Status:** Draft for product and engineering planning\
**Launch market:** Malawi\
**Initial platform:** Responsive website\
**Initial property scope:** Rentals and property sales, including
houses, apartments, land/plots, and commercial property

------------------------------------------------------------------------

## 1. Executive summary

Zonse Homes is a Malawi-focused property marketplace that helps people
discover properties to rent or buy, land and plots for sale, and
commercial spaces. It connects prospective tenants and buyers with
property owners, landlords, agents, and developers. The initial product
is a responsive website designed for mobile-first use, low-bandwidth
conditions, and a broad range of devices.

The MVP should make it easy to publish and find useful listings while
building trust through clear listing status, user reporting, moderation,
and carefully described verification checks. It should not claim that a
property is legally safe or that an advertiser owns a property unless
the relevant evidence has actually been reviewed through an appropriate
process.

Zonse Homes should be designed as one product in a larger Zonse
ecosystem. Use reusable identity, account, notification, and audit
foundations where practical, but avoid coupling the MVP to future
payment or marketplace apps before those products are ready.

### Product vision

**Help people in Malawi find property and connect with the right people,
with clearer information and more trust.**

### MVP outcomes

1.  A visitor can search and filter rental and sale listings without
    creating an account.
2.  A user can open a listing, understand the key facts, and contact the
    advertiser.
3.  An approved advertiser can create and manage listings.
4.  Administrators can review listings, respond to reports, suspend
    accounts, and maintain an audit trail.
5.  The site is usable on mobile, handles poor connections gracefully,
    and protects personal data.
6.  The technical foundation can support future maps, messaging, viewing
    bookings, subscriptions, and property management without a full
    rewrite.

------------------------------------------------------------------------

## 2. Goals and non-goals

### Goals

-   Launch a useful marketplace for both rentals and sales from day one.
-   Support homes, apartments, land/plots, and commercial properties.
-   Provide location-based discovery using Malawi-relevant
    administrative and neighbourhood descriptions.
-   Keep the core search experience open to anonymous visitors.
-   Establish a reliable listing lifecycle and moderation workflow.
-   Enable advertisers to manage listings without administrator
    intervention for routine edits.
-   Create a foundation for later integration with other Zonse products.
-   Make operational performance measurable from launch.

### Non-goals for MVP

Do not include these in the first public release unless a clear business
need emerges:

-   Holding, transferring, or escrow of rent, deposits, or purchase
    money.
-   Mortgage origination or credit scoring.
-   Legal conveyancing or definitive title certification.
-   Automated property valuation presented as authoritative.
-   Native iOS or Android applications.
-   Complex AI recommendations or conversational search.
-   Full tenancy, maintenance, and accounting management.
-   Public reviews or ratings of individuals.
-   Live chat that requires real-time infrastructure before the core
    marketplace is proven.

These can be considered in later phases.

------------------------------------------------------------------------

## 3. Target users and roles

### 3.1 Public visitor

Can: - Browse and search approved, active listings. - Filter and sort
results. - View listing details and advertiser public profiles. - Use
advertiser-provided phone or WhatsApp contact links, subject to privacy
controls. - Report a suspicious listing through a protected form.

Cannot: - Publish listings. - Access private account or moderation data.

### 3.2 Registered property seeker

Can do everything a public visitor can, plus: - Save and remove
favourite listings. - Manage basic profile and contact preferences. -
Submit reports and view confirmation that a report was received. - In a
later release, save searches and receive alerts.

Account creation should not be required merely to search.

### 3.3 Individual advertiser / property owner / landlord

Can: - Create a public advertiser profile. - Draft, submit, edit, pause,
and archive their own listings. - Upload property photos. - View listing
status and moderation feedback. - Respond to enquiries through the
contact methods they have enabled. - Mark a property as rented, sold, or
unavailable. - Request a review if a listing is rejected.

An advertiser's self-declared role must not be treated as proof of
ownership.

### 3.4 Real-estate agent or agency

Can: - Manage an agency profile and public contact details. - Create and
manage listings associated with their account. - In a later release, add
team members and manage multiple agents. - See basic listing views and
enquiry counts after analytics are implemented.

MVP can use one account per advertiser or agency. Team permissions can
be deferred.

### 3.5 Developer / commercial advertiser

Can publish multiple residential developments, commercial properties, or
land listings, subject to moderation and plan limits. Bulk upload and
project pages are post-MVP unless a launch partner requires them.

### 3.6 Moderator

Can: - Review submitted listings and edits flagged for review. -
Approve, reject, request changes, hide, or remove listings. - Review
user reports. - Record a reason and internal notes. - Escalate suspected
fraud to an administrator.

Cannot change system roles or alter audit history.

### 3.7 Administrator

Can: - Manage accounts and roles. - Manage listing categories and
location data. - Configure moderation rules and listing limits. -
Suspend or restore accounts. - Review audit logs and operational
dashboards. - Manage reported content and moderator access.

Administrative actions must be logged.

------------------------------------------------------------------------

## 4. Core user journeys

### Journey A: Find a rental

1.  Visitor opens the homepage.
2.  Selects **Rent**.
3.  Enters a location, property type, price range, and optional bedroom
    count.
4.  Views results as cards; map view can be added after the initial
    search experience is reliable.
5.  Opens a listing and reviews price, availability, photos, location,
    facilities, and advertiser status.
6.  Contacts the advertiser by phone or WhatsApp.
7.  Optionally signs in to save the property.

### Journey B: Buy a house or plot

1.  Visitor selects **Buy**.
2.  Chooses property type, such as house, apartment, land/plot, or
    commercial.
3.  Filters by location, budget, and size where applicable.
4.  Opens a listing and reviews available ownership/verification notes.
5.  Contacts the advertiser and arranges a viewing or further checks.
6.  The platform clearly states that listing information is supplied by
    the advertiser and that users should independently verify material
    claims.

### Journey C: Publish a listing

1.  Advertiser registers and verifies control of their email or phone
    where supported.
2.  Completes a public profile and selects advertiser type.
3.  Starts a listing and chooses intent: rent or sale.
4.  Enters required property details and location.
5.  Uploads photos; the system validates file type, size, and count.
6.  Previews the listing and submits it.
7.  Listing enters moderation queue.
8.  Moderator approves, rejects, or requests changes.
9.  Approved listing becomes searchable and the advertiser receives a
    status notification.
10. Advertiser can edit, pause, mark rented/sold, or archive it.
    Material edits may return the listing to review.

### Journey D: Report a suspicious listing

1.  Visitor or signed-in user selects **Report listing**.
2.  Selects a reason and provides optional detail.
3.  The report is rate-limited and stored privately.
4.  Moderator reviews the report and relevant listing history.
5.  Moderator may dismiss, request evidence, hide the listing, or
    escalate.
6.  Reporter sees only an appropriate acknowledgement, not private
    enforcement details.

------------------------------------------------------------------------

## 5. Functional requirements

Priority definitions: - **P0:** Required for MVP launch. - **P1:** High
value, implement after the core flow is stable. - **P2:** Later
enhancement.

### 5.1 Discovery and search

  -----------------------------------------------------------------------
  ID                      Requirement             Priority
  ----------------------- ----------------------- -----------------------
  DISC-01                 Public visitors can     P0
                          browse approved and     
                          active listings without 
                          signing in.             

  DISC-02                 Search supports keyword P0
                          and location terms.     

  DISC-03                 Filters include intent  P0
                          (rent/sale), property   
                          type, price range, and  
                          location.               

  DISC-04                 Property-specific       P0
                          filters are shown only  
                          where relevant,         
                          e.g. bedrooms for       
                          houses/apartments and   
                          land area for plots.    

  DISC-05                 Results can be sorted   P0
                          by newest and price     
                          ascending/descending.   

  DISC-06                 Pagination or           P0
                          cursor-based loading    
                          prevents loading all    
                          listings at once.       

  DISC-07                 Empty states suggest    P0
                          changing filters or     
                          clearing search.        

  DISC-08                 Users can save          P1
                          favourites after        
                          signing in.             

  DISC-09                 Map-based discovery and P1
                          radius search.          

  DISC-10                 Saved searches and      P1
                          alerts.                 
  -----------------------------------------------------------------------

### 5.2 Listing creation and management

  -----------------------------------------------------------------------
  ID                      Requirement             Priority
  ----------------------- ----------------------- -----------------------
  LIST-01                 Advertisers can create, P0
                          edit, preview, submit,  
                          pause, and archive      
                          their own listings.     

  LIST-02                 Every listing has       P0
                          rent/sale intent,       
                          property type, title,   
                          description,            
                          price/currency,         
                          location, and           
                          advertiser.             

  LIST-03                 Rent listings support   P0
                          rental period and       
                          required deposit/fees   
                          where known.            

  LIST-04                 Sale listings support   P0
                          asking price and        
                          negotiability.          

  LIST-05                 Property types include  P0
                          house, apartment/flat,  
                          land/plot, commercial,  
                          and other.              

  LIST-06                 Fields vary by property P0
                          type; e.g. bedrooms,    
                          bathrooms, land area,   
                          building area,          
                          utilities, and access.  

  LIST-07                 Listing photos are      P0
                          validated and safely    
                          processed.              

  LIST-08                 Listings have a status  P0
                          and status-change       
                          history.                

  LIST-09                 Expiration or periodic  P1
                          reconfirmation prevents 
                          stale listings.         

  LIST-10                 Bulk listing tools for  P2
                          large                   
                          agencies/developers.    
  -----------------------------------------------------------------------

### 5.3 Accounts and profiles

  -----------------------------------------------------------------------
  ID                      Requirement             Priority
  ----------------------- ----------------------- -----------------------
  USER-01                 Users can register,     P0
                          sign in, sign out, and  
                          recover access          
                          securely.               

  USER-02                 Public profiles show    P0
                          only approved public    
                          contact details and     
                          profile information.    

  USER-03                 Role and ownership      P0
                          checks are enforced on  
                          the server for every    
                          protected operation.    

  USER-04                 Users can update        P0
                          profile and privacy     
                          preferences.            

  USER-05                 Users can request       P1
                          account deletion,       
                          subject to legally      
                          required record         
                          retention.              

  USER-06                 Optional phone          P1
                          verification supports   
                          account trust but does  
                          not imply property      
                          ownership.              
  -----------------------------------------------------------------------

### 5.4 Contact and enquiries

  -----------------------------------------------------------------------
  ID                      Requirement             Priority
  ----------------------- ----------------------- -----------------------
  CONT-01                 Listing page provides   P0
                          the advertiser's        
                          enabled contact         
                          methods.                

  CONT-02                 Phone numbers and       P0
                          WhatsApp URLs are       
                          validated and safely    
                          formatted.              

  CONT-03                 Contact details can be  P1
                          hidden until the user   
                          chooses to reveal them, 
                          if advertiser prefers.  

  CONT-04                 In-app enquiries and    P1
                          message history.        

  CONT-05                 Viewing appointment     P1
                          requests and reminders. 
  -----------------------------------------------------------------------

### 5.5 Trust, safety, and moderation

  -----------------------------------------------------------------------
  ID                      Requirement             Priority
  ----------------------- ----------------------- -----------------------
  TRUST-01                New listings enter a    P0
                          review queue before     
                          public publication.     

  TRUST-02                Users can report        P0
                          listings using          
                          structured reason       
                          codes.                  

  TRUST-03                Moderators can approve, P0
                          reject, request         
                          changes, hide, and      
                          remove listings.        

  TRUST-04                Moderator actions       P0
                          require a reason and    
                          are audit-logged.       

  TRUST-05                Public verification     P0
                          labels explain exactly  
                          what was checked.       

  TRUST-06                Rate limits and         P0
                          anti-spam controls      
                          protect registration,   
                          listing creation, and   
                          reports.                

  TRUST-07                Duplicate and           P1
                          suspicious listing      
                          signals are surfaced to 
                          moderators.             

  TRUST-08                Document review         P1
                          workflows for           
                          ownership/authority     
                          evidence.               

  TRUST-09                Appeals and moderation  P1
                          service-level           
                          reporting.              
  -----------------------------------------------------------------------

### 5.6 Administration

  -----------------------------------------------------------------------
  ID                      Requirement             Priority
  ----------------------- ----------------------- -----------------------
  ADMIN-01                Admin dashboard shows   P0
                          listing counts by       
                          status, reports, and    
                          moderation backlog.     

  ADMIN-02                Admin can manage        P0
                          categories and location 
                          reference data.         

  ADMIN-03                Admin can               P0
                          suspend/restore         
                          accounts and disable    
                          listings.               

  ADMIN-04                Audit log records       P0
                          privileged actions.     

  ADMIN-05                Admin can review abuse  P1
                          patterns and export     
                          limited operational     
                          reports.                
  -----------------------------------------------------------------------

------------------------------------------------------------------------

## 6. Screen inventory and navigation

### Public website

1.  **Homepage**
    -   Brand header, Rent/Buy selector, search input, popular
        locations, property categories, recently approved listings,
        trust guidance.
    -   Avoid large autoplay media and heavy animation.
2.  **Search results**
    -   Search term and active filters.
    -   Result count, sort control, filter drawer on mobile.
    -   Listing cards with primary photo, price, location, key facts,
        status/verification labels.
    -   Pagination or "load more."
3.  **Listing details**
    -   Photo gallery, title, price, intent, property type, location,
        facts, description, fees, amenities, advertiser profile, contact
        actions, report button, similar listings.
    -   Display "last updated" and "availability last confirmed" when
        available.
    -   Clear disclaimer for unverified claims.
4.  **Advertiser profile**
    -   Public name, advertiser type, profile image/logo, contact
        options, active listings, verification labels.
5.  **Sign in / register / recovery**
    -   Minimal fields, accessible validation, abuse protections.
6.  **Create/edit listing wizard**
    -   Step 1: Rent or sale.
    -   Step 2: Property type.
    -   Step 3: Details and price.
    -   Step 4: Location.
    -   Step 5: Photos.
    -   Step 6: Contact preferences.
    -   Step 7: Preview and submit.
    -   Save drafts and clearly show required fields.
7.  **Advertiser dashboard**
    -   Drafts, pending review, published, changes requested, rejected,
        paused, rented/sold, archived.
    -   Create listing, edit, duplicate draft, and view moderation
        notes.
8.  **Favourites**
    -   Saved listings and clear unavailable/removed states.
9.  **Report listing**
    -   Reason, optional description, confirmation, abuse prevention.
10. **Help and safety**
    -   How to avoid scams, what verification labels mean, safe viewing
        guidance, contact and dispute channels.

### Admin and moderator screens

1.  Dashboard and queue counts.
2.  Listing review detail with full history and media.
3.  Reports queue.
4.  User/advertiser profile and listing history.
5.  Moderation action form with reason and internal notes.
6.  Location/category management.
7.  Audit log and role management (admin only).

### Suggested top-level navigation

-   Home
-   Rent
-   Buy
-   List a property
-   Saved (signed-in users)
-   Sign in / profile

Use one responsive web application rather than separate desktop and
mobile sites.

------------------------------------------------------------------------

## 7. Malawi-specific product decisions

### Location model

Support structured fields where possible, without assuming every
property has a formal street address:

-   Country (default Malawi)
-   Region
-   District
-   City/town
-   Neighbourhood/area
-   Optional landmark or directions
-   Optional latitude/longitude
-   Public location precision: exact, approximate, or neighbourhood-only

For privacy and safety, do not expose exact coordinates for every
residence by default. A property advertiser should be able to show an
approximate map location while sharing exact directions privately.

Location names should be managed as reference data with aliases and
spelling variants. Avoid hard-coding a fixed list of neighbourhoods
throughout the application.

### Currency and price

-   Store monetary amounts as integer minor units or a fixed-precision
    decimal; never use floating-point arithmetic for money.
-   Store ISO currency code (`MWK`) with each price.
-   Display prices with clear formatting and no ambiguous shorthand.
-   For rentals, require rental period (e.g. weekly, monthly, yearly)
    and allow a disclosed deposit or fee amount where known.
-   Support "price on request" only where moderation and product policy
    permit it.
-   Do not silently convert foreign currency into MWK.

### Connectivity and performance

-   Compress and resize images into multiple responsive sizes.
-   Lazy-load below-the-fold images.
-   Use pagination and cache public listing data.
-   Keep the first page light and avoid autoplay video.
-   Preserve form drafts when feasible.
-   Display clear retry states for upload or network errors.

### Trust and local context

-   Do not treat a phone number, ID document, or agent profile as proof
    of title.
-   If ownership or authority documents are reviewed, record who
    reviewed them, when, what type of evidence was checked, and the
    limits of that review.
-   Do not publish private identity documents.
-   Use plain-language safety guidance that advises buyers/renters to
    independently check ownership, authority to let/sell, boundaries,
    fees, and relevant legal requirements before paying or signing.

------------------------------------------------------------------------

## 8. Data model

Use a relational database, preferably PostgreSQL. The following is a
logical starting model; refine field types and constraints during
implementation.

### 8.1 `users`

-   `id` UUID primary key
-   `email` nullable, unique when present
-   `phone_e164` nullable, unique when verified/present
-   `auth_provider_id` or external auth subject
-   `status` (`active`, `suspended`, `pending_deletion`)
-   `created_at`, `updated_at`, `last_login_at`

Do not store plaintext passwords if using a managed identity provider.
If implementing authentication directly, use a proven password hashing
library and well-reviewed session handling.

### 8.2 `profiles`

-   `id` UUID primary key
-   `user_id` foreign key to users
-   `display_name`
-   `profile_type` (`individual`, `owner_landlord`, `agent`, `agency`,
    `developer`)
-   `bio` nullable
-   `avatar_media_id` nullable
-   `public_phone` nullable
-   `public_email` nullable
-   `whatsapp_number` nullable
-   `contact_preferences` JSONB or normalized fields
-   `verification_status` (`unverified`, `in_review`,
    `verified_limited`, `rejected`)
-   `created_at`, `updated_at`

"Verified" must refer to a defined check, not an unrestricted general
trust claim.

### 8.3 `listings`

-   `id` UUID primary key
-   `owner_user_id` foreign key to users
-   `profile_id` foreign key to profiles
-   `intent` (`rent`, `sale`)
-   `property_type` (`house`, `apartment`, `land_plot`, `commercial`,
    `other`)
-   `title`
-   `description`
-   `price_amount` fixed precision / integer minor units
-   `currency_code` (default `MWK`)
-   `price_negotiable` boolean
-   `rental_period` nullable (`weekly`, `monthly`, `yearly`, `other`)
-   `deposit_amount` nullable
-   `bedrooms` nullable
-   `bathrooms` nullable
-   `land_area_value` nullable
-   `land_area_unit` nullable
-   `building_area_value` nullable
-   `building_area_unit` nullable
-   `amenities` JSONB or normalized association table
-   `utilities` JSONB or normalized association table
-   `status` (`draft`, `pending_review`, `changes_requested`,
    `published`, `rejected`, `paused`, `rented`, `sold`, `expired`,
    `removed`, `archived`)
-   `published_at` nullable
-   `available_from` nullable
-   `availability_confirmed_at` nullable
-   `expires_at` nullable
-   `created_at`, `updated_at`

Add database checks for valid price, intent/property-type combinations
where needed, and status transitions in service logic.

### 8.4 `listing_locations`

-   `id` UUID primary key
-   `listing_id` unique foreign key to listings
-   `country_code`
-   `region`
-   `district`
-   `city_town`
-   `neighbourhood`
-   `landmark_directions` nullable
-   `latitude` nullable
-   `longitude` nullable
-   `public_precision` (`exact`, `approximate`, `neighbourhood`)
-   `created_at`, `updated_at`

Use PostGIS if radius and spatial queries become a core requirement; it
is not necessary for a first text-based search MVP.

### 8.5 `media_assets`

-   `id` UUID primary key
-   `uploaded_by_user_id`
-   `storage_key` (never expose private storage paths)
-   `media_type`
-   `mime_type`
-   `byte_size`
-   `width`, `height` nullable
-   `processing_status` (`pending`, `ready`, `rejected`)
-   `moderation_status`
-   `created_at`

### 8.6 `listing_media`

-   `listing_id`
-   `media_asset_id`
-   `display_order`
-   `is_cover`
-   Composite key or unique constraint on listing/media pair.

### 8.7 `listing_status_history`

-   `id` UUID primary key
-   `listing_id`
-   `from_status`
-   `to_status`
-   `changed_by_user_id` nullable for system action
-   `reason_code`
-   `internal_note` nullable
-   `created_at`

### 8.8 `favourites`

-   `user_id`
-   `listing_id`
-   `created_at`
-   Unique constraint on (`user_id`, `listing_id`).

### 8.9 `reports`

-   `id` UUID primary key
-   `listing_id` nullable
-   `reported_user_id` nullable
-   `reporter_user_id` nullable for guest reports
-   `reason_code` (`suspected_scam`, `duplicate`, `misleading_details`,
    `wrong_price`, `unavailable`, `inappropriate_content`, `other`)
-   `description` nullable
-   `status` (`new`, `investigating`, `actioned`, `dismissed`,
    `escalated`)
-   `assigned_to_user_id` nullable
-   `resolution_code` nullable
-   `created_at`, `resolved_at` nullable

### 8.10 `verification_checks`

-   `id` UUID primary key
-   `subject_type` (`profile`, `listing`, `ownership_evidence`)
-   `subject_id`
-   `check_type`
-   `status` (`pending`, `passed`, `failed`, `expired`, `needs_review`)
-   `reviewed_by_user_id` nullable
-   `evidence_reference` private storage reference, nullable
-   `review_notes` private, nullable
-   `checked_at`, `expires_at` nullable

Limit access to evidence. Avoid putting ID numbers or document contents
into logs.

### 8.11 `audit_logs`

-   `id` UUID primary key
-   `actor_user_id` nullable
-   `action`
-   `entity_type`
-   `entity_id`
-   `reason_code` nullable
-   `metadata` JSONB with carefully allow-listed fields
-   `ip_hash` or minimized security context where justified
-   `created_at`

Audit logs should be append-only for normal application roles and must
not contain passwords, tokens, or unnecessary personal data.

### 8.12 Supporting tables

Add as required: - `locations` and `location_aliases` - `categories` /
`amenities` - `moderation_queue` or queue derived from listing status -
`notifications` - `subscriptions` and `payments` only when paid plans
are implemented - `enquiries` when in-app enquiries are introduced -
`saved_searches` when alerts are introduced

### Relationship overview

-   One user can own one or more profiles only if the product permits
    it; MVP can simplify to one profile per user.
-   One profile can have many listings.
-   One listing has one location record and many media records.
-   Users can favourite many listings.
-   Listings can have many reports, status-history events, and
    verification checks.
-   Privileged actions create audit log records.

------------------------------------------------------------------------

## 9. API design

Use a versioned REST API (`/api/v1`) unless the selected framework
strongly favours another approach. Return consistent JSON, validate
inputs on the server, and document the contract with OpenAPI.

### Public endpoints

-   `GET /api/v1/listings`
    -   Query params: `intent`, `propertyType`, `region`, `district`,
        `city`, `neighbourhood`, `minPrice`, `maxPrice`, `bedrooms`,
        `sort`, `cursor`, `limit`, `q`.
    -   Only return published, active, non-expired listings.
    -   Validate sort keys and cap page size.
-   `GET /api/v1/listings/:id`
    -   Return public listing details and safe public advertiser fields.
    -   Do not expose private verification evidence or internal
        moderation notes.
-   `GET /api/v1/profiles/:id`
    -   Return public profile and active listings.
-   `GET /api/v1/locations`
    -   Return location reference data and aliases for
        search/autocomplete.

### Authenticated user endpoints

-   `POST /api/v1/auth/register`
-   `POST /api/v1/auth/login` or managed-auth equivalent
-   `POST /api/v1/auth/logout`
-   `POST /api/v1/auth/recovery`
-   `GET /api/v1/me`
-   `PATCH /api/v1/me`
-   `GET /api/v1/me/favourites`
-   `POST /api/v1/me/favourites/:listingId`
-   `DELETE /api/v1/me/favourites/:listingId`

### Advertiser endpoints

-   `POST /api/v1/listings`
-   `PATCH /api/v1/listings/:id`
-   `POST /api/v1/listings/:id/submit`
-   `POST /api/v1/listings/:id/pause`
-   `POST /api/v1/listings/:id/mark-rented`
-   `POST /api/v1/listings/:id/mark-sold`
-   `POST /api/v1/listings/:id/archive`
-   `POST /api/v1/listings/:id/media`
-   `DELETE /api/v1/listings/:id/media/:mediaId`
-   `GET /api/v1/me/listings`

Every mutation must verify that the signed-in user owns the listing or
has the relevant delegated permission.

### Reporting and moderation endpoints

-   `POST /api/v1/listings/:id/reports`
-   `GET /api/v1/admin/moderation/listings`
-   `POST /api/v1/admin/listings/:id/approve`
-   `POST /api/v1/admin/listings/:id/request-changes`
-   `POST /api/v1/admin/listings/:id/reject`
-   `POST /api/v1/admin/listings/:id/hide`
-   `GET /api/v1/admin/reports`
-   `POST /api/v1/admin/reports/:id/resolve`
-   `POST /api/v1/admin/users/:id/suspend`
-   `GET /api/v1/admin/audit-logs`

All `/admin` routes require server-enforced moderator/admin permissions.
Do not rely on hiding admin controls in the frontend.

### API conventions

-   Use consistent error format: `code`, user-safe `message`, optional
    field-level `details`, and a request ID.
-   Use appropriate HTTP status codes.
-   Add idempotency keys for future payment-related operations, not
    every MVP endpoint.
-   Use cursor pagination for large datasets or stable page-based
    pagination for the earliest MVP.
-   Add request validation schemas and API contract tests.
-   Never return stack traces, database errors, private media URLs, or
    internal notes to public clients.

------------------------------------------------------------------------

## 10. Recommended technical architecture

The MVP should use a **modular monolith**, not microservices. It is
simpler to develop, test, deploy, and operate with a small team while
still separating concerns in code.

### Suggested stack

This is a recommendation, not a requirement:

-   **Frontend:** Next.js with TypeScript and a responsive component
    system.
-   **Backend:** Next.js server routes/server actions for a small MVP,
    or a separately structured Node.js API if clear separation is
    preferred. Avoid maintaining two backend patterns without a reason.
-   **Database:** PostgreSQL.
-   **ORM/query layer:** Prisma or Drizzle; choose one and standardize
    migrations.
-   **Authentication:** A reputable managed authentication provider or a
    carefully implemented server-side session system.
-   **Media storage:** S3-compatible object storage with private upload
    flow and image processing.
-   **Image processing:** Server-side resize, metadata stripping, and
    format conversion.
-   **Hosting:** A reputable managed web host plus managed PostgreSQL
    and object storage. Choose deployment regions and providers based on
    data protection, latency, cost, and operational capability.
-   **Email:** Transactional email provider for verification and
    moderation notifications.
-   **Monitoring:** Error tracking, structured logs, uptime checks, and
    basic performance metrics.
-   **Testing:** Unit, integration, API authorization, and browser
    end-to-end tests.

### Logical modules

1.  Identity and profiles
2.  Property catalogue
3.  Search and discovery
4.  Media pipeline
5.  Listing workflow and moderation
6.  Reports and trust
7.  Notifications
8.  Admin operations
9.  Analytics and audit

Modules can live in one repository and deployment, but should have clear
boundaries and service interfaces.

### Request flow

1.  Browser requests a page or API endpoint.
2.  Server validates query or body.
3.  Authentication and authorization are checked where required.
4.  Domain logic enforces listing status transitions and rules.
5.  Database query runs with appropriate indexes.
6.  Media is served through a CDN or controlled object-storage URLs.
7.  Security-relevant and administrative actions are logged.
8.  Errors are monitored without leaking private information.

### Search approach

For MVP, use PostgreSQL text search and indexed structured filters. Do
not introduce a dedicated search engine before volume or relevance
requirements justify it. Search should prioritize published listings and
use deterministic sorting with a stable tie-breaker.

Potential indexes: -
`listings(status, intent, property_type, published_at)` -
`listings(price_amount)` -
`listing_locations(region, district, city_town, neighbourhood)` -
Full-text index over title and description -
`favourites(user_id, created_at)` - `reports(status, created_at)` -
Foreign-key indexes for common joins

Use composite indexes based on observed query plans rather than adding
every possible index in advance.

------------------------------------------------------------------------

## 11. Security and privacy requirements

Security is a release requirement, not a later enhancement.

### Authentication and authorization

-   Use a proven authentication provider or established session library.
-   Prefer secure, HTTP-only, same-site cookies for browser sessions
    where appropriate.
-   Enforce authorization on the server for every private record and
    mutation.
-   Prevent insecure direct object reference (IDOR) issues by checking
    ownership on each listing operation.
-   Require multi-factor authentication for administrators if supported.
-   Rate-limit sign-in, recovery, registration, uploads, and report
    submission.
-   Use least-privilege roles and separate moderator from administrator
    permissions.

### Input and web security

-   Validate and normalize all inputs on the server.
-   Escape output and sanitize any permitted rich text.
-   Use parameterized queries or safe ORM query APIs.
-   Apply CSRF protections when using cookie-based authentication.
-   Use a restrictive Content Security Policy and appropriate security
    headers.
-   Restrict CORS to the required origins.
-   Protect against stored and reflected XSS, SQL injection, SSRF, and
    malicious uploads.
-   Keep secrets in environment/secret management services, never in
    source control or frontend bundles.

### Media upload security

-   Allow only required image types.
-   Check actual file signatures rather than trusting file extensions or
    browser MIME type.
-   Limit file size, image dimensions, and number of files.
-   Re-encode images and strip EXIF metadata, especially GPS
    coordinates.
-   Generate storage keys server-side.
-   Store private verification documents separately from public listing
    photos.
-   Do not execute uploaded content.
-   Add malware scanning where feasible.
-   Use short-lived signed upload/download URLs where private access is
    needed.

### Personal data

-   Collect only data necessary for the service.
-   Explain what is public on profiles and listings.
-   Never publish identity or ownership documents.
-   Define retention and deletion policies for reports, audit logs, and
    verification evidence.
-   Restrict access to private documents and record access where
    appropriate.
-   Prepare a privacy notice and terms before public launch.
-   Review applicable Malawi data-protection, consumer-protection,
    electronic-transactions, and real-estate obligations with qualified
    local advisers.

### Operational security

-   Enforce TLS.
-   Patch dependencies and run automated vulnerability scanning.
-   Back up the database and test restoration.
-   Monitor failed logins, unusual listing volume, and repeated reports.
-   Have an incident response plan for account compromise, data
    exposure, and fraudulent listings.
-   Do not place tokens, full phone numbers, identity documents, or
    sensitive message content in application logs.

------------------------------------------------------------------------

## 12. Moderation policy and workflow

### Listing statuses

-   `draft`: not submitted and private to advertiser.
-   `pending_review`: submitted and awaiting moderation.
-   `changes_requested`: advertiser must amend the listing.
-   `published`: approved and visible in public search.
-   `rejected`: not approved; reason provided to advertiser.
-   `paused`: advertiser has temporarily hidden the listing.
-   `rented`: advertiser marked the rental unavailable due to tenancy.
-   `sold`: advertiser marked the property sold.
-   `expired`: no longer considered current.
-   `removed`: removed by moderation or policy enforcement.
-   `archived`: retained for advertiser history but not public.

### Required review checks

Moderators should check: - Required fields and price consistency. -
Category and intent correctness. - Spam, prohibited content, misleading
claims, and duplicate images/text. - Whether the listing appears to be
an attempt to impersonate another owner or agent. - Whether public
contact information appears abusive or suspicious. - Whether the claimed
verification label is supported by the verification record.

Moderators should not claim to have confirmed legal title unless a
defined, competent process has established that specific fact.

### Report reasons

-   Suspected scam or impersonation
-   Duplicate listing
-   Wrong price or misleading information
-   Property unavailable
-   Inappropriate or discriminatory content
-   Suspicious payment request
-   Other

### Enforcement ladder

1.  Request corrections for incomplete or unclear listings.
2.  Reject content that fails publication standards.
3.  Temporarily hide listings when credible risk requires investigation.
4.  Suspend accounts for repeated abuse or credible fraud signals.
5.  Escalate severe cases for specialist/legal review where appropriate.
6.  Maintain internal reasons, evidence references, timestamps, and
    appeal outcomes.

Do not automatically ban users based solely on the number of reports;
use reports as signals for review.

### Verification labels

Use precise labels, for example: - **Email confirmed** - **Phone
confirmed** - **Agent identity reviewed** - **Documents reviewed ---
scope explained**

Avoid an ambiguous universal **Verified Property** badge unless the
exact checks and their limitations are clearly defined.

------------------------------------------------------------------------

## 13. Non-functional requirements and acceptance criteria

### Performance

-   Core public pages should be usable on a typical mobile connection.
-   Use responsive images and lazy loading.
-   Establish a target of p75 Largest Contentful Paint at or below 2.5
    seconds on representative supported devices and network conditions,
    then measure in production.
-   Public search should target p95 API response under 800 ms for
    ordinary indexed queries at initial expected load, excluding slow
    third-party services. Revisit based on actual traffic.
-   Avoid loading large media until needed.

### Reliability and recovery

-   Target 99.5% monthly availability during early launch, with clear
    monitoring and incident ownership.
-   Automated database backups.
-   Perform a restore test before launch and on a recurring schedule.
-   Define a basic recovery point and recovery time objective
    appropriate to early-stage operations.

### Accessibility and usability

-   Target WCAG 2.2 AA for core journeys where practical.
-   Keyboard-accessible navigation and forms.
-   Visible focus states, labels, contrast, alt text, and useful error
    messages.
-   Responsive layout for narrow screens.
-   Clear empty, loading, success, and failure states.

### Data integrity

-   No listing becomes public unless it is in `published` status.
-   Every moderation status transition is validated server-side and
    recorded.
-   A user cannot edit or archive another user's listing.
-   A public API never returns internal moderation notes or private
    evidence.
-   Prices and currency are stored consistently.
-   Removed or expired listings disappear from search and sitemap
    output.

### MVP launch acceptance checklist

-   [ ] Anonymous user can search rentals and sale properties.
-   [ ] Filters work in combination and invalid values are rejected.
-   [ ] Advertiser can create a draft and submit a listing.
-   [ ] Submitted listing is not publicly visible until approved.
-   [ ] Moderator can approve, reject, request changes, and hide a
    listing.
-   [ ] Advertiser can edit only their own listings.
-   [ ] Report flow works and reports reach the moderation queue.
-   [ ] Upload validation rejects unsupported and oversized files.
-   [ ] Public pages do not leak private contact or verification data.
-   [ ] Sign-in and recovery protections are tested.
-   [ ] Key journeys work on mobile and desktop.
-   [ ] Database backup and restoration have been tested.
-   [ ] Privacy notice, terms, safety guidance, and support contact are
    published.
-   [ ] Monitoring, error reporting, and incident contacts are
    configured.

------------------------------------------------------------------------

## 14. Testing strategy

### Unit tests

Test: - Price and rental-period validation. - Listing status transition
rules. - Permission predicates. - Location normalization. - Filter
parsing and sort allow-list. - Verification-label rendering rules.

### Integration tests

Test: - User/profile/listing creation. - Listing submission and
moderation. - Media metadata and association. - Favourites. - Reporting
and resolution. - Audit log generation. - Public API redaction of
private fields.

### Authorization and security tests

Explicitly test: - User A cannot edit, pause, archive, or view private
drafts belonging to User B. - Non-moderator cannot call moderation
endpoints. - Moderator cannot grant themselves administrator
privileges. - Anonymous visitors cannot access private media or
evidence. - Malformed uploads and oversized requests are rejected. -
Search filters cannot bypass `published` status. - Rate limits operate
on abuse-prone endpoints.

### End-to-end tests

Automate the following browser flows: 1. Search for a rental and open a
listing. 2. Search for a property for sale and filter by location and
price. 3. Register, create a listing, and submit it. 4. Moderator
approves listing; listing appears publicly. 5. Moderator requests
changes; advertiser edits and resubmits. 6. User reports a listing;
moderator resolves it. 7. Advertiser marks a listing rented or sold; it
no longer appears as available. 8. Mobile navigation and listing
creation are usable at small screen widths.

### Release gates

Block release on: - Any critical/high-severity security issue. - Broken
authorization tests. - Data loss or migration failure. - Public leakage
of private evidence. - Core search or listing publication regressions.

------------------------------------------------------------------------

## 15. Phased implementation plan

The schedule below is an initial planning estimate for a small, focused
team. Actual duration depends on team size, existing code, design
readiness, provider setup, and test coverage.

### Phase 0 --- Product and technical foundation (1 week)

Deliverables: - Confirm requirements and launch geography. - Define
listing categories, mandatory fields, status transitions, and moderation
policy. - Create user flows and responsive wireframes. - Select hosting,
database, authentication, and media storage. - Establish repository,
environments, CI, migrations, and coding conventions. - Create privacy
and security checklist.

Exit criteria: - Product scope signed off. - Architecture decision
record created. - Data model and API contract reviewed.

### Phase 1 --- Public discovery (1--2 weeks)

Deliverables: - Responsive homepage. - Public listing cards and detail
page. - Rent/sale selector. - Search, location and property-type
filters. - Price sorting and pagination. - Seed data for development
only.

Exit criteria: - Anonymous search works across rentals and sales. - Only
published active listings are public. - Mobile performance is measured.

### Phase 2 --- Accounts and advertiser tools (1--2 weeks)

Deliverables: - Registration, sign-in and recovery. - Public profiles. -
Create/edit listing wizard. - Photo upload pipeline. - Advertiser
dashboard and listing statuses. - Ownership enforcement and server-side
validation.

Exit criteria: - Advertiser can submit and manage their own listings. -
Unauthorized access tests pass.

### Phase 3 --- Moderation, reporting and launch safety (1--2 weeks)

Deliverables: - Admin/moderator dashboard. - Review queue and action
reasons. - Reports workflow. - Status history and audit logs. - Rate
limiting and abuse controls. - Safety pages, terms, privacy notice and
support process.

Exit criteria: - Every submitted listing is reviewed before
publication. - Reports can be investigated and resolved. - Security and
end-to-end tests pass.

### Phase 4 --- Closed beta and launch preparation (1 week)

Deliverables: - Recruit a small group of legitimate owners and agents. -
Seed real listings only with permission and appropriate evidence. - Test
on real mobile devices and constrained connections. - Fix usability and
performance issues. - Backups, restore test, monitoring and incident
runbook. - Soft-launch checklist.

Exit criteria: - No critical launch blockers. - Moderation capacity and
support ownership are clear. - Core user journeys work end-to-end.

### Phase 5 --- Post-launch improvements (ongoing)

Suggested order: 1. Favourites and saved searches. 2. Listing freshness
reminders and expiry. 3. Viewing requests and in-app enquiries. 4. Agent
subscriptions and featured listings. 5. Map search and geospatial
filtering. 6. Structured verification/document review. 7. Property
management. 8. Carefully scoped integration with Zonse Pay. 9.
AI-assisted search and duplicate detection.

------------------------------------------------------------------------

## 16. Suggested team ownership

A small team can cover multiple roles, but every responsibility should
have an owner.

  -----------------------------------------------------------------------
  Responsibility                      Owner
  ----------------------------------- -----------------------------------
  Product scope and priorities        Product owner

  UX, responsive design and           Product designer / frontend lead
  accessibility                       

  Frontend implementation             Frontend developer

  API, data model and business rules  Backend developer

  Infrastructure, CI/CD, backups and  Technical lead / DevOps owner
  monitoring                          

  Moderation policy and queue         Operations/moderation lead
  operations                          

  Security and privacy review         Technical lead plus qualified
                                      external advice where needed

  User acceptance and beta feedback   Product owner and pilot users
  -----------------------------------------------------------------------

For a very small team, one developer may own frontend and backend. Keep
deployment and security tasks explicitly assigned rather than treating
them as nobody's responsibility.

------------------------------------------------------------------------

## 17. Analytics and success metrics

Track product performance without collecting unnecessary personal data.

### Marketplace health

-   Number of active published listings.
-   Listings by region, property type, and intent.
-   Percentage of listings with complete required details.
-   Percentage of listings reconfirmed as available.
-   Duplicate or reported listing rate.

### User outcomes

-   Search-to-listing-detail click-through rate.
-   Listing-detail-to-contact action rate.
-   Favourite usage after launch.
-   Enquiries or viewing requests per listing after those features
    launch.
-   Search sessions with zero results.

### Operations and trust

-   Median and p95 time to first moderation decision.
-   Pending-review backlog.
-   Report acknowledgement and resolution time.
-   Appeal/reversal rate.
-   Repeat policy violations.
-   Percentage of listings with accurately described verification
    checks.

### Business metrics

-   Advertiser activation and retention.
-   Listings per active advertiser.
-   Conversion to paid advertiser plan once monetization exists.
-   Revenue per paying advertiser.
-   Cost of media storage and serving per active listing.

Set numeric business targets after a pilot establishes a credible
baseline. Do not optimize raw listing count at the expense of quality or
safety.

------------------------------------------------------------------------

## 18. Deployment and environments

Maintain at least: - **Development:** local development with seeded,
non-personal data. - **Staging:** production-like environment for QA and
moderator training. - **Production:** restricted access, monitored,
backed up.

Use: - Automated linting, type checks, unit tests, and migration checks
in CI. - Reviewed database migrations. - Separate secrets per
environment. - No production data copied into development without a
privacy-approved process. - A rollback strategy for application releases
and a tested recovery strategy for database changes. - Dependency
lockfiles and periodic dependency updates.

### Initial repository structure

A reasonable starting point for a Next.js modular monolith:

``` text
/apps
  /web
    /app
    /components
    /features
      /auth
      /profiles
      /listings
      /search
      /favourites
      /reports
      /moderation
    /lib
      /auth
      /db
      /validation
      /security
      /storage
/packages
  /ui
  /shared
  /config
/prisma-or-db
  /migrations
/tests
  /unit
  /integration
  /e2e
/docs
  PRD.md
  API.md
  SECURITY.md
  MODERATION.md
```

This is illustrative. If a simpler repository is better for the chosen
stack, keep the same module boundaries without adding unnecessary
workspace complexity.

------------------------------------------------------------------------

## 19. Key risks and mitigations

  -----------------------------------------------------------------------
  Risk                                Mitigation
  ----------------------------------- -----------------------------------
  Fraudulent or misleading property   Pre-publication moderation,
  listings                            reports, clear verification labels,
                                      audit trail, and rapid hiding
                                      capability.

  Too few quality listings at launch  Recruit pilot agents/owners,
                                      provide a clear listing workflow,
                                      and focus initial marketing
                                      geographically.

  Stale listings                      Availability confirmation, expiry,
                                      and easy status updates.

  Low-bandwidth usability             Responsive images, lightweight
                                      pages, pagination, and performance
                                      monitoring.

  Exposure of personal or ownership   Private storage, strict access
  documents                           controls, retention limits, and no
                                      public document URLs.

  Unauthorized listing edits          Server-side ownership checks and
                                      automated IDOR tests.

  Scope creep                         Treat maps, AI, payments,
                                      subscriptions, and full property
                                      management as phased work.

  Dependency on a single developer    Documentation, code review,
                                      migration discipline, automated
                                      tests, and runbooks.

  Confusing verification claims       Define each check precisely and
                                      show its scope and date.

  Legal or regulatory uncertainty     Obtain appropriate local advice
                                      before collecting sensitive
                                      evidence or handling transaction
                                      money.
  -----------------------------------------------------------------------

------------------------------------------------------------------------

## 20. Decisions to confirm before development

1.  Initial geographic coverage: all Malawi from day one, or begin with
    Lilongwe and expand after the pilot?
2.  Will advertisers be allowed to publish immediately after email/phone
    verification, or must every listing be manually reviewed?
    Recommendation: manual review before first publication during MVP.
3.  Which contact methods are mandatory: phone, WhatsApp, or either?
    Recommendation: require at least one valid contact method, but allow
    the advertiser to control what is publicly displayed.
4.  What exact evidence, if any, will support public verification
    labels? Recommendation: launch with basic account/identity checks
    only if a defined process exists; do not claim title verification
    without a suitable process.
5.  Who will handle daily moderation, reports, and user support?
6.  Will listing creation be free during beta? Recommendation: keep it
    free initially and introduce paid visibility or professional plans
    only after the marketplace has useful inventory and demand.
7.  Which authentication, hosting, database, and media providers fit the
    available budget and team skills?

------------------------------------------------------------------------

## Final recommendation

Build Zonse Homes as a **responsive, mobile-first modular monolith**
with PostgreSQL, a proven authentication approach, object storage for
media, and a strong moderation workflow. Launch with rentals and sales
together, but keep the MVP focused on the full listing lifecycle:
**discover → inspect → contact** for seekers, and **create → submit →
get approved → manage** for advertisers.

Do not start with payments, AI, microservices, or elaborate investment
tools. Prove that the marketplace can attract real properties, help
users contact legitimate advertisers, keep listings fresh, and respond
to fraud reports. Those are the foundations that make the later Zonse
ecosystem valuable.



---

# 21. Account Centre and Account Settings Requirements Addendum

## 21.1 Purpose and scope

Zonse Homes MUST provide a comprehensive, first-class Account Centre within the public Zonse Homes web application. The Account Centre is the central place where authenticated users manage their personal information, account identity, business or agency information, privacy, security, preferences, verification information and account lifecycle.

Account Settings MUST provide the configuration controls that determine how a user's account and Zonse Homes experience behave. It may be implemented as a dedicated area within the Account Centre, but its navigation and purpose must be clear to users.

These capabilities apply to individual users, property seekers, individual property advertisers, landlords, registered businesses, real-estate agencies and other supported account types.

This addendum supplements the existing requirements in Sections 3, 4, 5, 6, 8, 9, 11, 13, 14 and 15. Where the existing PRD mentions only basic profile editing, registration or account recovery, this addendum expands those requirements into a complete account-management experience.

All requirements in this addendum form part of the planned Zonse Homes product. P0 and P1 priorities must be completed and verified before the planned product launch. P1 denotes implementation priority, not permission to omit a requirement from the completed product.

The Account Centre is for ordinary Zonse Homes users. It MUST NOT be confused with or merged into the separate private administrative application. Administrative account management, moderation, platform configuration and privileged operational controls remain within the separately secured Admin application.

## 21.2 Account Centre information architecture

The Account Centre MUST be accessible to authenticated users through the signed-in account/profile navigation.

It MUST provide a clear, responsive and accessible structure covering the following areas:

1. Account overview.
2. Personal profile and personal information.
3. Account type and business/agency information, where applicable.
4. Privacy and public-profile visibility.
5. Contact preferences.
6. Notifications and communication preferences.
7. Security and active sessions.
8. Verification and trust information.
9. Language, regional and experience preferences.
10. Listing and advertiser defaults, where applicable.
11. Connected services and social accounts, when the relevant integrations are implemented.
12. Personal-data access and account lifecycle controls.

The interface MUST make it clear which settings affect:
- Private information visible only to the account owner.
- Information displayed on the user's public profile.
- Information displayed on the user's property listings.
- Information shared with other users through contact or enquiry features.
- Information used for authentication, security, verification or legal obligations.

The Account Centre MUST work on mobile and desktop screens and remain usable on lower-bandwidth connections.

## 21.3 Personal profile and information management

Users MUST be able to review and manage the personal information associated with their accounts.

Requirements:

- View and edit their display name and other supported personal profile details.
- Add, change or remove a profile photograph.
- Update their biography or profile description where supported.
- Update their email address and phone number.
- Review which personal details are private and which are publicly visible.
- Review the account type associated with their account.
- See when an update requires additional confirmation or verification.
- Receive clear confirmation when an account-information change succeeds or fails.

Changes to email addresses and phone numbers MUST follow an appropriate secure confirmation process before the new values are treated as confirmed. Sensitive changes MUST require appropriate reauthentication or additional verification.

A user MUST NOT be able to change another user's profile or account information.

The system MUST validate changes on the server, not rely solely on frontend validation.

## 21.4 Individual, corporate and agency account management

The Account Centre MUST support the account types defined in the PRD, including individual users and registered businesses or real-estate agencies.

For supported business and agency profiles, the Account Centre SHOULD provide management of relevant information such as:

- Registered business name.
- Trading or display name.
- Business or agency type.
- Registration or identification information, where applicable.
- Business description.
- Business logo or profile image.
- Business contact details.
- Business address and operating locations.
- Public-facing business information.
- Relevant supporting information required by the separate verification process.

The precise mandatory business fields and documentary requirements MUST follow applicable product and legal decisions for Malawi.

Where the product supports business account permissions or team membership, those permissions MUST be managed through explicit role-based authorisation. An ordinary profile editor MUST NOT automatically receive privileged account-management rights.

Changes to material business information may require renewed review. The system MUST preserve the distinction between editable business information and independently reviewed business certification.

Changing a business name, logo, address or other profile field MUST NOT automatically grant, preserve or remove a certified-business badge. Certification changes MUST occur only through the authorised verification workflow.

The system MUST preserve appropriate verification history and record material changes for audit purposes.

## 21.5 Privacy and public visibility settings

Users MUST have understandable controls over the personal and business information that Zonse Homes displays publicly.

Supported visibility controls SHOULD cover:

- Display name.
- Profile photograph.
- Biography or profile description.
- Phone number.
- Email address.
- WhatsApp or other supported contact details.
- Public business contact information.
- Other supported profile attributes.

Contact details MUST be private by default unless the user explicitly chooses to make particular details public.

Users MUST be able to review the consequences of enabling public visibility before saving the setting.

The platform MUST distinguish between:
- Public profile visibility.
- Contact visibility.
- Listing-specific contact visibility.
- Private information retained for account operation, security or verification.

A setting that hides information from public visitors MUST NOT prevent the platform from processing information required for legitimate account, security, verification, moderation or legal purposes.

The platform MUST never expose private verification documents, authentication credentials, session tokens or private account information through public profiles or listing APIs.

Privacy settings MUST be enforced by backend authorisation and response filtering. Hiding an element in the frontend alone is insufficient.

## 21.6 Contact preferences

Users MUST be able to configure their preferred supported contact methods.

These may include:
- In-platform messaging or enquiries.
- Phone calls.
- WhatsApp.
- Email.
- Other contact channels introduced by the product.

Users MUST be able to distinguish between making a contact method available and making the underlying contact detail publicly visible.

The platform MUST respect applicable privacy settings and listing-level contact controls when presenting contact options to other users.

Changes to contact preferences MUST NOT expose private contact information unexpectedly.

## 21.7 Notification and communication settings

The Account Centre MUST provide notification preferences for supported communication channels and notification categories.

Notification categories SHOULD distinguish between:

- Account and authentication security notifications.
- Important account activity.
- Property listing status and moderation updates.
- Enquiries and messages.
- Listing expiry, renewal and relevant listing activity.
- Payment and transaction updates.
- Verification requests and outcomes.
- Product announcements.
- Marketing and promotional communications.

Where supported, notification channels may include email, SMS, push notifications and in-platform notifications.

Users MUST be able to manage optional marketing and promotional communications separately from essential transactional, security and legally required communications.

Essential service, security and legal notifications MUST NOT be disabled where their delivery is necessary for the secure or lawful operation of the service.

The system MUST respect channel availability, consent and communication preferences. It MUST NOT display a notification option as available if the corresponding channel has not been implemented or enabled.

## 21.8 Account security and active sessions

The Account Centre MUST provide a dedicated security area.

Users MUST be able to:

- Change their password.
- Access the supported account-recovery process.
- Review relevant account-security information.
- View active sessions or signed-in devices.
- Revoke an individual session where supported.
- Sign out of other active sessions.
- Sign out of all sessions where supported.
- Review important security-related account activity where available.

Session information presented to users may include suitable metadata such as device or browser description and last-active time. Approximate location information MUST only be shown where it is reliably available and appropriate.

Raw session tokens, access tokens, refresh tokens, password hashes and other authentication secrets MUST never be exposed in the Account Centre.

Sensitive operations MUST require appropriate reauthentication or step-up verification.

The backend MUST enforce session ownership and revocation permissions. A user MUST NOT be able to inspect or revoke another user's sessions.

Password changes, account recovery, credential changes and session revocation MUST follow the security policy defined by the authentication implementation. The system MUST provide an appropriate way to invalidate compromised sessions.

## 21.9 Verification and trust information

The Account Centre MUST provide a clear view of the user's relevant verification and trust status.

The interface MUST distinguish separate verification dimensions, including where applicable:

- Email confirmation.
- Phone confirmation.
- Individual identity review.
- Agent identity review.
- Business or agency certification.
- Property-document review.
- Ownership or authority-to-market review.

The platform MUST NOT use one generic verification status to imply that all these checks have been completed.

Users SHOULD be able to see:
- Which checks are complete.
- Which checks are pending.
- Which checks require additional information.
- Which checks were unsuccessful.
- What action is required next, where applicable.

Where users can submit verification information, the interface MUST explain the purpose of the request and handle supporting evidence securely.

Private evidence MUST remain accessible only to appropriately authorised verification and administrative personnel.

Editing ordinary profile or business information MUST NOT automatically mark a verification check as complete.

A certified-business badge MUST retain the disclaimer and limitations already defined in the PRD. It MUST NOT imply ownership of a listed property, verified property title, accuracy of every listing or authority to market every property.

Verification decisions MUST remain separate from ordinary profile editing and MUST be recorded through the authorised verification workflow.

## 21.10 Language, regional and experience preferences

The Account Centre SHOULD support relevant user preferences, including where implemented:

- Preferred interface language.
- Country or region.
- Timezone.
- Currency display preference.
- Regional number, date and display formats.
- Accessibility or interface preferences where supported.

These settings MUST be based on supported product capabilities. The implementation MUST NOT offer unsupported languages, currencies or regional functionality as though they are already available.

The design MUST support Malawi as the initial market while allowing additional regions and locales to be introduced without redesigning the account-management architecture.

## 21.11 Listing and advertiser defaults

For users who publish property listings or advertisements, the Account Centre SHOULD provide appropriate reusable defaults where supported by the listing workflow.

Examples include:

- Preferred contact methods.
- Default contact visibility.
- Preferred listing location.
- Other reusable listing preferences that are explicitly supported by the product.

A default MUST NOT silently override a user's explicit choice when creating or editing an individual listing.

Listing-specific settings MUST remain distinguishable from general account settings.

The platform MUST enforce the privacy and authorisation rules defined for each listing independently of the user's default preferences.

## 21.12 Connected services and social accounts

The Account Centre MUST provide a dedicated area for connected third-party services when the corresponding integrations are implemented.

This requirement supports the planned ability for listing owners and advertisers to distribute their Zonse Homes listings to designated platforms, including Facebook, Instagram and WhatsApp.

The design MUST distinguish:

- Native device or browser share-sheet functionality.
- Manual sharing through a platform.
- Link and image sharing.
- Automated or authorised publishing through a connected third-party account.

Where third-party account connections are supported, users MUST be able to understand:
- Which service is connected.
- Which permissions have been granted.
- What actions Zonse Homes is authorised to perform.
- How to disconnect or revoke the connection.

Third-party authorisation MUST use the supported secure authorisation mechanism. Tokens and credentials MUST be protected and MUST NOT be exposed to the frontend or ordinary account-profile responses.

The system MUST NOT publish content to a user's connected account without the required user authorisation and applicable platform permissions.

Disconnecting a service MUST revoke or invalidate the applicable connection and prevent further authorised publishing through that connection.

The social publishing capability MUST preserve the previously specified product behaviour: listing distribution should use the relevant user-published property imagery and direct viewers to the corresponding Zonse Homes listing page where supported.

Native sharing and manual sharing MUST remain available as appropriate fallbacks when direct platform publishing is unavailable or not authorised.

## 21.13 Personal-data access and account activity

Users MUST have an appropriate way to request or access a copy of their personal account data, subject to security, privacy and applicable legal restrictions.

The platform SHOULD provide access to relevant account information and account-related activity where appropriate.

The implementation MUST define:
- Which personal data can be accessed directly.
- Which data requires a formal request.
- How the user's identity is confirmed before disclosure.
- How the data is delivered securely.
- How third-party information and legally restricted records are protected.

The PRD does not prescribe a particular export file format. That decision may be made during detailed implementation planning.

Account activity presented to users MUST be limited to information they are authorised to see. Internal moderation notes, private verification evidence, privileged administrative records and security secrets MUST NOT be exposed.

## 21.14 Account deactivation and deletion

The Account Centre MUST distinguish temporary account deactivation from permanent account deletion requests.

### Deactivation

Where supported, users SHOULD be able to request temporary deactivation.

The product MUST define the effect of deactivation on:
- Sign-in and account access.
- Public profile visibility.
- Active listings.
- Contact and enquiry functionality.
- Existing transactions or obligations.
- Restoration or reactivation.

Deactivation MUST NOT silently destroy data that is required to restore the account or meet legal obligations.

### Deletion

Users MUST be able to initiate an account-deletion request through an appropriately secured workflow.

The deletion process MUST:
- Clearly explain the consequences.
- Require suitable confirmation.
- Protect against accidental or unauthorised deletion.
- Apply the platform's documented retention and legal-obligation rules.
- Handle personal data deletion or anonymisation appropriately.
- Preserve records that must legally or operationally be retained, with appropriate access restrictions and minimisation.
- Address relevant listings, messages, payments, verification records and other associated data according to the retention policy.
- Communicate the request's status and outcome where appropriate.

The platform MUST NOT promise that all records will be erased where applicable law, financial obligations, fraud prevention, security or audit requirements require limited retention.

Deletion and deactivation MUST be auditable and MUST be enforced by the backend.

## 21.15 Data model and backend capabilities

The existing `users`, `profiles`, `verification_checks` and `audit_logs` entities remain the foundation for account management.

The implementation MUST inspect and reuse existing identity, authentication, profile, session and token models before introducing additional tables. It MUST avoid duplicate representations of data or duplicate session-management mechanisms.

The complete data model MUST support the requirements in this addendum. Depending on the existing implementation, supporting entities or fields may include:

- User account preferences.
- Privacy and visibility preferences.
- Notification preferences and channel consent.
- Account-security and session metadata, reusing the existing session implementation.
- Account lifecycle and deletion requests.
- Business or agency profile information.
- Social-account connection metadata and protected authorisation credentials.
- Relevant account activity and audit records.

These are logical data requirements, not instructions to create every item as a separate database table. The final schema MUST follow the established SQLAlchemy and Alembic architecture and existing data ownership boundaries.

The implementation MUST preserve referential integrity, appropriate indexes, server-side validation and access controls.

Sensitive values MUST be encrypted or otherwise protected as appropriate. Secrets, credentials and private evidence MUST NOT be stored in plaintext or exposed through ordinary API responses.

## 21.16 API requirements

The Account Centre MUST be supported by authenticated, versioned backend APIs.

The existing `/api/v1/me` and profile endpoints SHOULD be extended where appropriate rather than introducing duplicate account APIs.

The complete API design MUST provide capabilities for:

- Reading the authenticated user's account overview.
- Updating permitted personal profile information.
- Updating and confirming email and phone changes.
- Managing supported business or agency profile information.
- Reading and updating privacy and visibility preferences.
- Managing contact preferences.
- Reading and updating notification preferences.
- Changing passwords through the secure authentication workflow.
- Listing and revoking the authenticated user's sessions.
- Reading verification status and submitting supported verification requests.
- Managing supported language and regional preferences.
- Managing supported listing defaults.
- Connecting and disconnecting authorised third-party services.
- Requesting and retrieving permitted personal-data exports.
- Initiating and reviewing account deactivation or deletion requests.

The exact route structure and request/response schemas MUST be reconciled with the existing backend API architecture. The route examples and capabilities in this addendum describe required behaviour; they do not assert that these endpoints already exist.

All account-management endpoints MUST:
- Require authentication where appropriate.
- Enforce ownership and role permissions server-side.
- Validate and constrain submitted fields.
- Apply rate limits to sensitive operations.
- Use appropriate confirmation and reauthentication requirements.
- Return only data the requesting user is authorised to access.
- Avoid leaking internal security or verification information.

## 21.17 Security, privacy and audit requirements

The Account Centre MUST comply with the security and privacy principles already defined in Section 11.

Additional requirements:

- Sensitive account changes MUST require appropriate reauthentication or step-up verification.
- Email and phone changes MUST be confirmed before the new values are considered verified.
- Password and session operations MUST use the established authentication and session-security implementation.
- Session revocation MUST take effect on the backend.
- Account-management operations MUST enforce ownership and prevent insecure direct object references.
- Privacy preferences MUST be enforced by API responses and backend business logic.
- Connected-service authorisation credentials MUST be protected and access restricted.
- Private verification evidence MUST remain private.
- Account deletion and deactivation MUST follow defined lifecycle and retention policies.
- Security-sensitive and material account changes MUST be audit logged.
- Audit logs MUST be append-only or otherwise protected against unauthorised alteration.
- Audit metadata MUST be minimised and MUST NOT contain passwords, raw tokens, private evidence or unnecessary personal information.
- Users MUST NOT be able to alter verification outcomes, audit records or privileged account attributes through ordinary account settings.

## 21.18 Screen inventory and navigation additions

The existing screen inventory in Section 6 MUST be extended to include:

1. Account Centre overview.
2. Personal profile and information editor.
3. Business or agency profile editor.
4. Privacy and visibility settings.
5. Contact preferences.
6. Notification preferences.
7. Security settings.
8. Active sessions and device management.
9. Verification and trust status.
10. Language and regional preferences.
11. Listing and advertiser defaults.
12. Connected services and social accounts.
13. Personal-data access.
14. Account deactivation and deletion workflow.

These areas may be organised into a coherent Account Centre rather than implemented as fourteen unrelated pages. The final navigation MUST be understandable, responsive and accessible.

The signed-in navigation MUST provide a clear route to the Account Centre. Users MUST be able to return to their listings and other relevant account activities without losing their place unnecessarily.

## 21.19 Acceptance criteria

The Account Centre and Account Settings requirements MUST NOT be considered complete until the following behaviours are implemented and verified:

- An authenticated user can access their Account Centre.
- A user can update permitted personal profile information.
- Email and phone changes follow secure confirmation.
- Individual and business/agency account information is handled according to account permissions.
- Public and private profile information is correctly separated.
- Contact details remain private by default unless the user explicitly enables public visibility.
- Notification preferences work according to supported channels and essential-notification rules.
- Users can securely change passwords.
- Users can inspect and revoke their own sessions according to supported capabilities.
- Users cannot inspect or modify another user's account or sessions.
- Verification information is displayed accurately and separately by verification type.
- Editing profile information cannot independently grant or remove business certification or property verification.
- Supported language, regional and listing preferences are saved and respected.
- Connected services can be reviewed and disconnected securely when implemented.
- Personal-data access requests follow the defined authorisation and disclosure process.
- Account deactivation and deletion requests follow the defined lifecycle and retention policy.
- Private evidence, credentials, session tokens and restricted administrative information are never exposed through public or ordinary account APIs.
- Account-management actions are appropriately validated and audited.
- The Account Centre works on supported mobile and desktop layouts.
- The separate Admin application remains independent.

## 21.20 Testing requirements

The testing strategy in Section 14 MUST be extended to cover Account Centre functionality.

Tests MUST include:

### Functional tests
- Account overview retrieval.
- Personal profile updates.
- Business and agency profile updates.
- Privacy and visibility preferences.
- Contact preferences.
- Notification preferences.
- Regional and language preferences.
- Listing defaults.
- Verification status display.
- Data-access requests.
- Deactivation and deletion workflows.

### Authentication and security tests
- Unauthenticated access is rejected where required.
- Users cannot access another user's account data.
- Users cannot access or revoke another user's sessions.
- Sensitive changes enforce the required reauthentication or confirmation.
- Email and phone changes cannot bypass confirmation.
- Session revocation invalidates the relevant session.
- Password changes follow the established credential-security policy.
- Connected-service credentials and tokens are not exposed.
- Private verification evidence is not exposed.
- Account deletion and lifecycle actions enforce ownership and confirmation.

### Privacy and authorisation tests
- Private contact information is not returned publicly.
- Public profile visibility follows the user's saved preferences.
- Listing-specific contact visibility is respected.
- Business certification cannot be granted through profile editing.
- Verification status cannot be modified by ordinary account settings.
- Audit records cannot be modified by ordinary users.
- Essential notifications remain enabled where required.

### Integration and end-to-end tests
- A user can complete the relevant Account Centre journeys from the web interface through the backend.
- Account changes persist and are reflected consistently across the application.
- Session and authentication changes are reflected in subsequent requests.
- Account lifecycle workflows behave correctly with associated listings and records.
- Connected-service workflows respect authorisation and revocation when implemented.

The test suite MUST include negative and permission-boundary cases, not just successful user journeys.

## 21.21 Implementation and completion requirements

The Account Centre and Account Settings MUST be included in the relevant account and profile implementation scope in Section 15.

The implementation MUST build on the existing identity and authentication foundations rather than replacing or duplicating them.

The work MUST be coordinated with the relevant profile, verification, listing, messaging, notification, payment, social integration and privacy capabilities.

Social account connections MUST be implemented in coordination with the social distribution and publishing functionality. They MUST not be represented as complete merely because a placeholder settings screen exists.

The Account Centre MUST be treated as a real product capability with functioning backend enforcement, persistence, frontend controls, security and tests. A visual-only implementation is insufficient.

All applicable P0 and P1 Account Centre requirements MUST be completed and verified as part of the full planned Zonse Homes system before launch.

The existing project architecture, technology decisions, milestone structure, security boundaries and deployment timing remain unchanged by this addendum. Implementation planning MUST continue to use the authoritative development milestones and existing project requirements.
