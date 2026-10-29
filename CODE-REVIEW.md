# Code review: Zonse Homes front-end v0.1

## Summary

The prototype is structured cleanly. Money is stored as whole numbers, unpublished listings are filtered out in the search logic, and contact links are built from digits only. Several items are missing for a public launch, mainly data loading, error states and the report flow.

## Issues

| # | File | Issue | Severity | Status |
|---|---|---|---|---|
| 1 | `data/listings.js` | Sample data is bundled into the app. Public visitors need it fetched from the API. | Medium | Open. Replace with API call. |
| 2 | `App.jsx` | Route lives in component state, so pages have no shareable URL and the back button does not work. | Medium | Open. Decided in ADR-0001. |
| 3 | `pages/Listing.jsx` | "Report this listing" is disabled. PRD TRUST-02 requires it. | High for launch | Open. Phase 3. |
| 4 | `pages/*` | No loading, error or retry states (PRD section 13). | Medium | Open. |
| 5 | `components/ListingCard.jsx` | Photos are colour blocks. PRD requires responsive, lazy-loaded images. | Medium | Open. |
| 6 | `lib/search.js` | Malformed numbers are ignored silently. Acceptable for now, but the UI should show a message. | Low | Open. |

## What looks good

- Unpublished listings are excluded inside `filterListings`, so the rule cannot be bypassed by the UI.
- Phone and WhatsApp links are built from digits and validated, so they cannot carry unexpected content.
- Verification badges name the exact check, in line with PRD section 12.
- Exact coordinates are not stored or displayed, and the location shows approximate wording.
- Bedrooms and land-area filters appear only for relevant property types (DISC-04).

## Verdict

**Approve for prototype and design review. Request changes before any real listing data is loaded.** Items 1, 3 and 4 must be resolved first.
