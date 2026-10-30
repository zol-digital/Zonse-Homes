export const defaultFilters = {
  intent: "rent",
  propertyType: "any",
  minPrice: "",
  maxPrice: "",
  bedrooms: "any",
  minArea: "",
  query: "",
  sort: "newest"
};

// Empty or malformed numbers are ignored instead of producing broken results.
const toNumber = value => {
  const n = Number(value);
  return value === "" || !Number.isFinite(n) || n < 0 ? null : n;
};

const SORTERS = {
  newest: (a, b) => b.publishedAt - a.publishedAt,
  priceAsc: (a, b) => a.price - b.price,
  priceDesc: (a, b) => b.price - a.price
};

export function filterListings(listings, f) {
  const q = f.query.trim().toLowerCase();
  const min = toNumber(f.minPrice);
  const max = toNumber(f.maxPrice);
  const beds = toNumber(f.bedrooms);
  const area = toNumber(f.minArea);

  return listings
    .filter(l => l.status === "published") // unpublished listings never appear in search (PRD 11)
    .filter(l => l.intent === f.intent)
    .filter(l => f.propertyType === "any" || l.propertyType === f.propertyType)
    .filter(l => min === null || l.price >= min)
    .filter(l => max === null || l.price <= max)
    .filter(l => beds === null || (l.bedrooms ?? 0) >= beds)
    .filter(l => area === null || (l.landArea ?? 0) >= area)
    .filter(l => !q || [l.title, l.district, l.neighbourhood].join(" ").toLowerCase().includes(q))
    .sort((a, b) => (SORTERS[f.sort] ?? SORTERS.newest)(a, b) || a.id.localeCompare(b.id));
}
