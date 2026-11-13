"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { CATEGORY_ICON, isPromoted, priceText, type Listing } from "@/lib/data";
import { useStore } from "@/lib/store";

export default function MinePage() {
  const { me, listings, deleteListing, promote } = useStore();
  const router = useRouter();

  if (!me) {
    return (
      <div className="empty">
        <div className="big">🏡</div>
        <p>Log in to manage your listings.</p>
        <br />
        <Link className="btn" href="/account">Log in</Link>
      </div>
    );
  }

  const mine = listings.filter((l) => l.owner === me.id);

  if (!mine.length) {
    return (
      <div className="empty">
        <div className="big">🏡</div>
        <p>You have not posted anything yet.</p>
        <br />
        <Link className="btn" href="/post">Post your first listing</Link>
      </div>
    );
  }

  function onDelete(l: Listing) {
    if (window.confirm(`Delete "${l.title}"? This cannot be undone.`)) deleteListing(l.id);
  }

  return (
    <>
      <h1 style={{ fontSize: "clamp(2rem, 4vw, 3rem)", marginBottom: 6 }}>My listings</h1>
      <p className="muted" style={{ marginBottom: 18 }}>Manage, promote or remove what you posted</p>

      <div className="stack">
        {mine.map((l) => (
          <div key={l.id} className="card" style={{ display: "flex", gap: 16, alignItems: "center", flexWrap: "wrap" }}>
            <div
              style={{
                width: 64, height: 64, borderRadius: 16, background: "var(--placeholder)",
                display: "grid", placeItems: "center", fontSize: 28, flexShrink: 0,
              }}
            >
              {CATEGORY_ICON[l.category]}
            </div>
            <div style={{ flex: 1, minWidth: 200 }}>
              <strong>{l.title}</strong>{" "}
              {isPromoted(l) && <span className="pill pill-ok">⭐ Promoted</span>}
              <div className="muted">{l.category} · {l.district} · {priceText(l)}</div>
              <div className="muted">
                {isPromoted(l) ? `Promoted until ${new Date(l.promoted).toLocaleDateString()}` : "Not promoted"}
              </div>
            </div>
            <div className="inline">
              <button className="btn btn-light btn-small" onClick={() => router.push(`/listing/${l.id}`)}>View</button>
              <button className="btn btn-small" onClick={() => promote(l.id, 7)}>⭐ Promote 7 days</button>
              <button className="btn btn-light btn-small" onClick={() => router.push(`/post?id=${l.id}`)}>Edit</button>
              <button className="btn btn-danger btn-small" onClick={() => onDelete(l)}>Delete</button>
            </div>
          </div>
        ))}
      </div>
    </>
  );
}