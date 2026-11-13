"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { CATEGORY_ICON, isPromoted, priceText, specsText } from "@/lib/data";
import { ratingFor, useStore } from "@/lib/store";
import { VerifiedBadge } from "@/components/VerifiedBadge";
import { ShareButton } from "@/components/ShareButton";
import { Reviews, Stars } from "@/components/Reviews";

const PLANS = [
  { days: 7, price: 5000 },
  { days: 30, price: 15000 },
];

export default function ListingPage() {
  const params = useParams<{ id: string }>();
  const id = params.id;
  const { listings, users, reviews, me, toggleFav, promote } = useStore();
  const router = useRouter();

  const l = listings.find((x) => x.id === id);

  if (!l) {
    return (
      <div className="empty">
        <div className="big">🧭</div>
        <p>We could not find that listing.</p>
        <br />
        <Link className="btn" href="/explore">Back to Explore</Link>
      </div>
    );
  }

  const owner = users.find((u) => u.id === l.owner);
  const mine = me?.id === l.owner;
  const saved = me?.favorites.includes(l.id) ?? false;
  const promoted = isPromoted(l);
  const { avg, count } = ratingFor(reviews, l.id);
  const mapSrc = `https://www.google.com/maps?q=${l.lat},${l.lng}&z=13&output=embed`;

  function onSave() {
    if (!toggleFav(l!.id)) router.push("/account");
  }

  function onMessage() {
    if (!me) return router.push("/account");
    router.push(`/messages?listing=${l!.id}`);
  }

  return (
    <>
      <div className="inline" style={{ marginBottom: 18 }}>
        <Link className="btn btn-light btn-small" href="/explore">← Back to Explore</Link>
        {promoted && <span className="pill pill-ok">⭐ Promoted</span>}
      </div>

      <div className="detail">
        <div>
          <div className="gallery">{CATEGORY_ICON[l.category]}</div>

          <div className="stats">
            {l.category !== "Land" && (
              <>
                <div>Bedrooms<strong>{l.beds}</strong></div>
                <div>Bathrooms<strong>{l.baths}</strong></div>
              </>
            )}
            <div>Size<strong>{l.area.toLocaleString()} m²</strong></div>
            <div>Type<strong>{l.category}</strong></div>
          </div>

          <h2 className="sec-head">About this listing</h2>
          <p className="muted" style={{ fontSize: 14, lineHeight: 1.7 }}>{l.description}</p>

          {l.features.length > 0 && (
            <>
              <h2 className="sec-head">Features</h2>
              <div className="feature-chips">
                {l.features.map((f) => (
                  <span key={f} className="chip">{f}</span>
                ))}
              </div>
            </>
          )}

          <h2 className="sec-head">📍 Location</h2>
          <iframe className="map-frame" title="Location map" loading="lazy" src={mapSrc} />
          <p style={{ marginTop: 8 }}>
            <a className="muted" href={`https://www.google.com/maps?q=${l.lat},${l.lng}`} target="_blank" rel="noopener noreferrer">
              Open in Google Maps ↗
            </a>
          </p>
        </div>

        <aside className="card side-card">
          <span className="pill">{l.purpose === "Rent" ? "For rent" : "For sale"} · {l.category}</span>
          <h2 style={{ fontSize: 26, margin: "12px 0 4px" }}>{l.title}</h2>
          <p className="muted">{l.district}, Malawi · {specsText(l)}</p>
          {count > 0 && (
            <p className="muted" style={{ marginTop: 6 }}>
              <Stars value={avg} /> {avg.toFixed(1)} · {count} {count === 1 ? "review" : "reviews"}
            </p>
          )}
          <div className="big-price">{priceText(l)}</div>
          <p className="muted" style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
            Listed by {owner ? owner.name : "Member"}{owner ? ` · ${owner.accountType}` : ""}
            {owner?.accountType === "Company" && owner.verified && <VerifiedBadge />}
          </p>

          <div className="stack" style={{ marginTop: 18 }}>
            {mine ? (
              <>
                <p className="muted">
                  {promoted
                    ? `Promoted until ${new Date(l.promoted).toLocaleDateString()}`
                    : "Not promoted. Promoted listings appear first."}
                </p>
                <div className="promo-options">
                  {PLANS.map((p) => (
                    <button key={p.days} className="btn btn-small" onClick={() => promote(l.id, p.days)}>
                      ⭐ {p.days} days · MWK {p.price.toLocaleString()}
                    </button>
                  ))}
                </div>
                <p className="muted" style={{ fontSize: 12 }}>Demo mode: payment is simulated.</p>
                <Link className="btn btn-light btn-full" href={`/post?id=${l.id}`}>✏️ Edit listing</Link>
              </>
            ) : (
              <button className="btn btn-full" onClick={onMessage}>💬 Message seller</button>
            )}
            <button className="btn btn-light btn-full" onClick={onSave}>
              {saved ? "♥ Saved" : "♡ Save listing"}
            </button>
            <ShareButton title={l.title} />
          </div>
        </aside>
      </div>

      <Reviews listingId={l.id} ownerId={l.owner} />
    </>
  );
}