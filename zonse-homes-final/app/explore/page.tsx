"use client";

import dynamic from "next/dynamic";
import { useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";
import { ListingCard } from "@/components/ListingCard";
import { DISTRICTS, isPromoted, type Category, type Purpose } from "@/lib/data";
import { useStore } from "@/lib/store";

// The map needs the browser, so it's loaded only on the client
const MapView = dynamic(() => import("@/components/MapView"), { ssr: false });

const PURPOSES: { value: "all" | Purpose; label: string }[] = [
  { value: "all", label: "All" },
  { value: "Rent", label: "Rent" },
  { value: "Sale", label: "For sale" },
];

const CATEGORIES: { value: "all" | Category; label: string }[] = [
  { value: "all", label: "All types" },
  { value: "House", label: "Houses" },
  { value: "Apartment", label: "Apartments" },
  { value: "Airbnb", label: "Airbnb" },
  { value: "Land", label: "Land" },
];

function ExploreInner() {
  const { listings } = useStore();
  const params = useSearchParams();
  const [q, setQ] = useState(params.get("q") ?? "");
  const [purpose, setPurpose] = useState<"all" | Purpose>("all");
  const [category, setCategory] = useState<"all" | Category>("all");
  const [district, setDistrict] = useState("all");
  const [sort, setSort] = useState("newest");

  const term = q.trim().toLowerCase();

  let list = listings.filter(
    (l) =>
      (purpose === "all" || l.purpose === purpose) &&
      (category === "all" || l.category === category) &&
      (district === "all" || l.district === district) &&
      (!term ||
        (l.title + " " + l.district + " " + l.category + " " + l.description)
          .toLowerCase()
          .includes(term))
  );

  if (sort === "price-low") list = [...list].sort((a, b) => a.price - b.price);
  else if (sort === "price-high") list = [...list].sort((a, b) => b.price - a.price);
  else list = [...list].sort((a, b) => b.created - a.created);

  // Promoted listings always appear first
  list = [...list].sort((a, b) => (isPromoted(b) ? 1 : 0) - (isPromoted(a) ? 1 : 0));

  return (
    <>
      <h1 style={{ fontSize: "clamp(2rem, 4vw, 3rem)", marginBottom: 6 }}>Explore</h1>
      <p className="muted" style={{ marginBottom: 18 }}>Every property on the map</p>

      <div className="filters">
        <input
          className="search-input"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Search houses, land, Airbnbs..."
          aria-label="Search"
        />
        <div className="filter-row">
          {PURPOSES.map((p) => (
            <button
              key={p.value}
              className={`chip ${purpose === p.value ? "active" : ""}`}
              onClick={() => setPurpose(p.value)}
            >
              {p.label}
            </button>
          ))}
        </div>
        <div className="filter-row">
          {CATEGORIES.map((c) => (
            <button
              key={c.value}
              className={`chip ${category === c.value ? "active" : ""}`}
              onClick={() => setCategory(c.value)}
            >
              {c.label}
            </button>
          ))}
        </div>
        <div className="filter-row">
          <select className="select" value={district} onChange={(e) => setDistrict(e.target.value)} aria-label="District">
            <option value="all">All districts</option>
            {Object.keys(DISTRICTS).map((d) => (
              <option key={d} value={d}>{d}</option>
            ))}
          </select>
          <select className="select" value={sort} onChange={(e) => setSort(e.target.value)} aria-label="Sort">
            <option value="newest">Last added</option>
            <option value="price-low">Price: low to high</option>
            <option value="price-high">Price: high to low</option>
          </select>
        </div>
      </div>

      <MapView listings={list} />

      <p className="result-count">{list.length} {list.length === 1 ? "property" : "properties"}</p>
      {list.length ? (
        <div className="grid">
          {list.map((l, i) => (
            <ListingCard key={l.id} listing={l} index={i} />
          ))}
        </div>
      ) : (
        <div className="empty">
          <div className="big">🔍</div>
          <p>No properties match. Try different filters.</p>
        </div>
      )}
    </>
  );
}

export default function ExplorePage() {
  return (
    <Suspense fallback={null}>
      <ExploreInner />
    </Suspense>
  );
}