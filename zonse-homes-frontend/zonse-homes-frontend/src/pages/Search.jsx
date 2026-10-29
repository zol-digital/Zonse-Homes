import { useMemo, useState } from "react";
import { Button } from "../components/Button.jsx";
import { FilterBar } from "../components/FilterBar.jsx";
import { ListingCard } from "../components/ListingCard.jsx";
import { defaultFilters, filterListings } from "../lib/search.js";

const PAGE_SIZE = 4;
const SORT_OPTIONS = [["newest", "Newest"], ["priceAsc", "Price: low to high"], ["priceDesc", "Price: high to low"]];

export default function Search({ listings, filters, onChange, onOpen }) {
  const [shown, setShown] = useState(PAGE_SIZE);
  const results = useMemo(() => filterListings(listings, filters), [listings, filters]);

  const update = next => {
    setShown(PAGE_SIZE);
    onChange(next);
  };

  return (
    <div className="page">
      <h1>{filters.intent === "rent" ? "Homes to rent" : "Property for sale"}</h1>
      <FilterBar filters={filters} onChange={update} />

      <div className="results-head">
        <p className="muted" aria-live="polite">
          {results.length} {results.length === 1 ? "result" : "results"}
          {filters.query && <> for “{filters.query}”</>}
        </p>
        <label>
          Sort
          <select value={filters.sort} onChange={e => update({ ...filters, sort: e.target.value })}>
            {SORT_OPTIONS.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
          </select>
        </label>
      </div>

      {results.length === 0 ? (
        <div className="empty">
          <h2>No matches yet</h2>
          <p className="muted">Try a higher maximum price, a different property type, or clear your filters.</p>
          <Button variant="secondary" onClick={() => update({ ...defaultFilters, intent: filters.intent })}>Clear filters</Button>
        </div>
      ) : (
        <>
          <div className="grid">
            {results.slice(0, shown).map(l => <ListingCard key={l.id} listing={l} onOpen={onOpen} />)}
          </div>
          {shown < results.length && (
            <div className="center more">
              <Button variant="secondary" onClick={() => setShown(s => s + PAGE_SIZE)}>Load more</Button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
