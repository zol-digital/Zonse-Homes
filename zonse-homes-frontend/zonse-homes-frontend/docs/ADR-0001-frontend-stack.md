# ADR-0001: Front-end framework for the Zonse Homes web app

**Status:** Proposed
**Date:** 26 October 2026
**Deciders:** Product owner, technical lead

## Context

PRD section 10 recommends Next.js with TypeScript. This phase asks for React with JSX so the design can be built and reviewed quickly. Public listing pages must be indexable by search engines and load well on slow mobile connections (PRD section 13).

## Decision

Build the design system and screens in a React and Vite project using JSX. Keep components free of routing and data fetching, so they can move into Next.js without a rewrite.

## Options considered

**A. React and Vite (JSX).** Fast to prototype and simple to run. Weakness: no server rendering, so public listing pages index poorly and the first load is heavier.

**B. Next.js (TypeScript).** Matches the PRD. Server rendering helps search visibility and low-bandwidth loading. More setup for this stage.

**C. Plain HTML and CSS.** No component reuse and harder to test. Rejected.

## Consequences

- Easier: design review, component documentation, quick iteration.
- Harder: search visibility and first-load speed on public pages; routing is state-based for now, so pages have no shareable URLs.
- Revisit before Phase 1 exit. Public pages will probably move to Next.js. Components are written to make that move mechanical.

## Action items

- [ ] Confirm framework with the technical lead before Phase 1
- [ ] Replace sample data with the `GET /api/v1/listings` contract
- [ ] Add real URLs for search and listing pages before launch
