import { useState } from "react";
import { Button } from "../components/Button.jsx";
import { ListingCard } from "../components/ListingCard.jsx";
import { defaultFilters } from "../lib/search.js";

const LOCATIONS = ["Lilongwe", "Blantyre", "Mzuzu", "Zomba", "Mangochi"];
const CATEGORIES = [["house", "Houses"], ["apartment", "Apartments"], ["land_plot", "Land & plots"], ["commercial", "Commercial"]];

export default function Home({ listings, onSearch, onOpen }) {
  const [intent, setIntent] = useState("rent");
  const [query, setQuery] = useState("");
  const search = patch => onSearch({ ...defaultFilters, intent, query, ...patch });
  const recent = listings.filter(l => l.status === "published").slice(0, 3);

  return (
    <div className="page">
      <section className="hero">
        <div>
          <p className="eyebrow">Malawi property, clearly listed</p>
          <h1>Find a place to live, or the right plot to build on.</h1>
        </div>
        <form className="search-card" onSubmit={e => { e.preventDefault(); search(); }}>
          <div className="segmented" role="group" aria-label="Rent or buy">
            {[["rent", "Rent"], ["sale", "Buy"]].map(([value, label]) => (
              <button key={value} type="button" aria-pressed={intent === value} className={intent === value ? "is-on" : ""} onClick={() => setIntent(value)}>
                {label}
              </button>
            ))}
          </div>
          <label className="sr-only" htmlFor="q">Location or keyword</label>
          <input id="q" className="search-input" placeholder="Area, district or keyword" value={query} onChange={e => setQuery(e.target.value)} />
          <Button type="submit">Search</Button>
        </form>
        <div className="chips" aria-label="Popular locations">
          {LOCATIONS.map(loc => <button key={loc} className="chip" onClick={() => search({ query: loc })}>{loc}</button>)}
        </div>
      </section>

      <section>
        <h2>Browse by type</h2>
        <div className="category-row">
          {CATEGORIES.map(([value, label]) => (
            <button key={value} className="category" onClick={() => search({ propertyType: value })}>{label}</button>
          ))}
        </div>
      </section>

      <section>
        <h2>Recently approved</h2>
        <div className="grid">
          {recent.map(l => <ListingCard key={l.id} listing={l} onOpen={onOpen} />)}
        </div>
      </section>

      <section className="trust">
        <h2>Before you pay or sign</h2>
        <p>Listing details come from advertisers. Check ownership, the authority to let or sell, boundaries, fees and any legal requirements yourself before you pay or sign.</p>
      </section>
    </div>
  );
}
