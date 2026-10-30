import { useState } from "react";
import { listings } from "./data/listings.js";
import { defaultFilters } from "./lib/search.js";
import { Button } from "./components/Button.jsx";
import Home from "./pages/Home.jsx";
import Search from "./pages/Search.jsx";
import Listing from "./pages/Listing.jsx";

export default function App() {
  const [route, setRoute] = useState({ name: "home" });
  const [filters, setFilters] = useState(defaultFilters);

  const go = (name, extra = {}) => {
    setRoute({ name, ...extra });
    window.scrollTo({ top: 0 });
  };
  const searchWith = patch => {
    setFilters(f => ({ ...f, ...patch }));
    go("search");
  };
  const openListing = id => go("listing", { id });
  const current = route.name === "listing" ? listings.find(l => l.id === route.id) : null;

  return (
    <>
      <header className="site-header">
        <button className="brand" onClick={() => go("home")}>Zonse Homes</button>
        <nav className="site-nav" aria-label="Main">
          {[["home", "Home"], ["search", "Find property"]].map(([key, label]) => (
            <button
              key={key}
              className={`nav-link ${route.name === key ? "is-current" : ""}`}
              aria-current={route.name === key ? "page" : undefined}
              onClick={() => go(key)}
            >
              {label}
            </button>
          ))}
          <Button variant="secondary" size="sm" disabled title="Available in Phase 2">List a property</Button>
          <Button variant="ghost" size="sm" disabled title="Available in Phase 2">Sign in</Button>
        </nav>
      </header>

      <main>
        {route.name === "search" && (
          <Search listings={listings} filters={filters} onChange={setFilters} onOpen={openListing} />
        )}
        {route.name === "listing" && current && (
          <Listing listing={current} onBack={() => go("search")} />
        )}
        {(route.name === "home" || (route.name === "listing" && !current)) && (
          <Home listings={listings} onSearch={searchWith} onOpen={openListing} />
        )}
      </main>
    </>
  );
}
