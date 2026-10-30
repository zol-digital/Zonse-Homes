# Zonse Homes Design System v0.1

Source of truth for tokens: `src/index.css`.

## Tokens

| Token | Value | Use |
|---|---|---|
| `--brand` | #0F4C3A | Primary actions, prices, links |
| `--accent` | #C8553D | Focus rings, trust notice |
| `--sand` / `--paper` | #F6F1E7 / #FFFDF8 | Page and surface backgrounds |
| `--ink` / `--muted` | #1D2320 / #5F6B65 | Text |
| `--success` | #2F7D57 | Verification labels |
| Display font | Source Serif 4 | Headings |
| Body font | Work Sans | Everything else |
| Spacing | 4, 8, 12, 16, 24, 40 px | Layout rhythm |
| Radius | 4 / 10 / 18 px | Deliberately varied by element size |
| Motion | 260 ms ease-out | Hover lift and transitions; disabled for reduced-motion users |

## Components

**Button** has primary, secondary and ghost variants and sm and md sizes. States: default, hover (lift), active (press), focus (accent outline), disabled (faded, no pointer).

**Badge** has neutral and success tones. Property type uses neutral. Verification uses success and must name the exact check (for example "Email confirmed"), never a general "Verified" label.

**ListingCard** shows photo, badges, title, neighbourhood and district only (never exact addresses), price and key facts. Hover lifts the card.

**FilterBar** shows a Rent/Buy segmented control, property type, price range, and bedrooms or minimum land area only when the chosen property type needs them.

## Patterns

- Search results: filter bar, result count (announced to screen readers), sort, grid, load more.
- Empty state: explains why there are no matches and offers a clear-filters action.
- Listing detail: facts grid, description, and a sticky side panel with price, verification and contact actions.
- Trust notice: shown on the home page and in listing detail.

## Accessibility

Visible focus on every control. Labels on every input. `aria-pressed` on toggles, `aria-current` on navigation, and `aria-live` on result counts. Brand text on paper is well above the 4.5:1 contrast minimum. Motion respects `prefers-reduced-motion`.

## Do and don't

| Do | Don't |
|---|---|
| Show prices as whole MWK amounts | Use floating-point money |
| Show approximate location unless exact is approved | Show exact coordinates by default |
| Name the scope of each verification check | Use an unexplained "Verified Property" badge |
| Keep the palette warm and earthy | Use purple gradients or default Inter styling |
