const TYPES = [["any", "Any type"], ["house", "House"], ["apartment", "Apartment"], ["land_plot", "Land / plot"], ["commercial", "Commercial"]];

export function FilterBar({ filters, onChange }) {
  const set = patch => onChange({ ...filters, ...patch });
  // Only show the filters that make sense for the chosen property type (PRD DISC-04).
  const showBedrooms = ["house", "apartment"].includes(filters.propertyType);
  const showLandArea = filters.propertyType === "land_plot";

  return (
    <section className="filter-bar" aria-label="Search filters">
      <div className="segmented" role="group" aria-label="Rent or buy">
        {[["rent", "Rent"], ["sale", "Buy"]].map(([value, label]) => (
          <button key={value} aria-pressed={filters.intent === value} className={filters.intent === value ? "is-on" : ""} onClick={() => set({ intent: value })}>
            {label}
          </button>
        ))}
      </div>
      <label>
        Property type
        <select value={filters.propertyType} onChange={e => set({ propertyType: e.target.value })}>
          {TYPES.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
        </select>
      </label>
      <label>
        Min price (MWK)
        <input type="number" min="0" inputMode="numeric" value={filters.minPrice} onChange={e => set({ minPrice: e.target.value })} />
      </label>
      <label>
        Max price (MWK)
        <input type="number" min="0" inputMode="numeric" value={filters.maxPrice} onChange={e => set({ maxPrice: e.target.value })} />
      </label>
      {showBedrooms && (
        <label>
          Bedrooms
          <select value={filters.bedrooms} onChange={e => set({ bedrooms: e.target.value })}>
            <option value="any">Any</option>
            <option value="1">1 or more</option>
            <option value="2">2 or more</option>
            <option value="3">3 or more</option>
          </select>
        </label>
      )}
      {showLandArea && (
        <label>
          Min land area (m²)
          <input type="number" min="0" inputMode="numeric" value={filters.minArea} onChange={e => set({ minArea: e.target.value })} />
        </label>
      )}
    </section>
  );
}
