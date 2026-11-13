"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import { useMemo, useState } from "react";
import { CATEGORY_ICON, isPromoted, priceText, specsText, type Listing, type Message } from "@/lib/data";
import { ratingFor, useStore } from "@/lib/store";

// The map needs the browser, so it's loaded only on the client
const MapView = dynamic(() => import("@/components/MapView"), { ssr: false });

type Filter = "all" | "sale" | "rent" | "airbnb";

const FILTERS: { value: Filter; label: string }[] = [
  { value: "all", label: "All" },
  { value: "sale", label: "For sale" },
  { value: "rent", label: "For rent" },
  { value: "airbnb", label: "Airbnb" },
];

export default function DashboardPage() {
  const { me, listings, users, messages, reviews, sendMessage, promote } = useStore();
  const [filter, setFilter] = useState<Filter>("all");
  const [q, setQ] = useState("");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [chatKey, setChatKey] = useState<string | null>(null);
  const [text, setText] = useState("");

  const meId = me?.id ?? "";

  // All hooks must run before the early return below
  const mine = useMemo(() => listings.filter((l) => l.owner === meId), [listings, meId]);
  const mineIds = useMemo(() => new Set(mine.map((l) => l.id)), [mine]);

  // Messages about my listings, from or to me
  const myMessages = useMemo(
    () => messages.filter((m) => mineIds.has(m.listingId) && (m.from === meId || m.to === meId)),
    [messages, mineIds, meId]
  );

  // One conversation per listing and person
  const convos = useMemo(() => {
    const map = new Map<string, { key: string; listingId: string; otherId: string; last: Message }>();
    myMessages.forEach((m) => {
      const otherId = m.from === meId ? m.to : m.from;
      const key = m.listingId + ":" + otherId;
      const prev = map.get(key);
      if (!prev || m.time > prev.last.time) {
        map.set(key, { key, listingId: m.listingId, otherId, last: m });
      }
    });
    return [...map.values()].sort((a, b) => b.last.time - a.last.time);
  }, [myMessages, meId]);

  const filtered = useMemo(() => {
    const term = q.trim().toLowerCase();
    return mine.filter((l) => {
      const typeOk =
        filter === "all" ||
        (filter === "sale" && l.purpose === "Sale") ||
        (filter === "rent" && l.purpose === "Rent" && l.category !== "Airbnb") ||
        (filter === "airbnb" && l.category === "Airbnb");
      const searchOk =
        !term || l.title.toLowerCase().includes(term) || l.district.toLowerCase().includes(term);
      return typeOk && searchOk;
    });
  }, [mine, filter, q]);

  if (!me) {
    return (
      <div className="empty">
        <div className="big">📊</div>
        <p>Log in to see your property dashboard.</p>
        <br />
        <Link className="btn" href="/account">Log in</Link>
      </div>
    );
  }

  const selected: Listing | null = mine.find((l) => l.id === selectedId) ?? filtered[0] ?? null;
  const activeChat = convos.find((c) => c.key === chatKey) ?? convos[0] ?? null;

  const thread = activeChat
    ? messages
        .filter(
          (m) =>
            m.listingId === activeChat.listingId &&
            ((m.from === meId && m.to === activeChat.otherId) ||
              (m.from === activeChat.otherId && m.to === meId))
        )
        .sort((a, b) => a.time - b.time)
    : [];

  function savesFor(id: string) {
    return users.filter((u) => u.favorites.includes(id)).length;
  }

  function enquiriesFor(id: string) {
    return new Set(myMessages.filter((m) => m.listingId === id && m.from !== meId).map((m) => m.from)).size;
  }

  // Engagement score out of 100, built from saves, enquiries, reviews, rating and promotion
  function scoreFor(l: Listing) {
    const r = ratingFor(reviews, l.id);
    const raw =
      savesFor(l.id) * 10 +
      enquiriesFor(l.id) * 15 +
      r.count * 5 +
      (r.avg / 5) * 20 +
      (isPromoted(l) ? 10 : 0);
    return Math.min(100, Math.round(raw));
  }

  const scored = mine.map((l) => ({ listing: l, score: scoreFor(l) })).sort((a, b) => b.score - a.score);
  const top = scored[0];
  const totalSaves = mine.reduce((sum, l) => sum + savesFor(l.id), 0);
  const totalEnquiries = mine.reduce((sum, l) => sum + enquiriesFor(l.id), 0);
  const promotedCount = mine.filter((l) => isPromoted(l)).length;
  const allRatings = mine.map((l) => ratingFor(reviews, l.id)).filter((r) => r.count > 0);
  const avgRating = allRatings.length
    ? allRatings.reduce((s, r) => s + r.avg, 0) / allRatings.length
    : 0;

  function sendReply() {
    if (!activeChat || !text.trim()) return;
    sendMessage(activeChat.listingId, activeChat.otherId, text);
    setText("");
  }

  function nameOf(id: string) {
    return users.find((u) => u.id === id)?.name ?? "Member";
  }

  return (
    <>
      {/* Header with action buttons */}
      <div className="dash-header">
        <div>
          <h1 style={{ fontSize: "clamp(2rem, 4vw, 3rem)", marginBottom: 6 }}>Dashboard</h1>
          <p className="muted">How your properties are doing</p>
        </div>
        <div className="dash-actions">
          <Link className="btn" href="/post">+ New listing</Link>
          <Link className="btn btn-light" href="/messages">Messages</Link>
        </div>
      </div>

      {/* Summary */}
      <div className="dash-summary">
        <div className="dash-stat"><strong>{mine.length}</strong><span>Listings</span></div>
        <div className="dash-stat"><strong>{totalEnquiries}</strong><span>Enquiries</span></div>
        <div className="dash-stat"><strong>{totalSaves}</strong><span>Times saved</span></div>
        <div className="dash-stat"><strong>{avgRating ? avgRating.toFixed(1) : "–"}</strong><span>Average rating</span></div>
        <div className="dash-stat"><strong>{promotedCount}</strong><span>Promoted</span></div>
      </div>

      {!mine.length ? (
        <div className="empty">
          <div className="big">🏡</div>
          <p>You have not posted anything yet.</p>
          <br />
          <Link className="btn" href="/post">Post your first listing</Link>
        </div>
      ) : (
        <>
          {/* Performance analytics */}
          <section className="dash-panel" style={{ marginBottom: 18 }}>
            <div className="dash-panel-head">
              <strong>Listing performance</strong>
              {top && top.score > 0 && (
                <span className="muted">Top performer: {top.listing.title} ({top.score}/100)</span>
              )}
            </div>
            <p className="muted" style={{ fontSize: 12, marginBottom: 14 }}>
              Score out of 100. Saves, enquiries, reviews, rating and promotion all add to it.
            </p>
            <div className="perf-table">
              <div className="perf-row perf-head">
                <span>Listing</span>
                <span>Saves</span>
                <span>Enquiries</span>
                <span>Reviews</span>
                <span>Score</span>
              </div>
              {scored.map(({ listing: l, score }) => {
                const r = ratingFor(reviews, l.id);
                return (
                  <div key={l.id} className="perf-row">
                    <span className="perf-name">
                      <strong>{l.title}</strong>
                      <span className="muted">{l.category} · {l.district}</span>
                    </span>
                    <span>{savesFor(l.id)}</span>
                    <span>{enquiriesFor(l.id)}</span>
                    <span>{r.count ? `★ ${r.avg.toFixed(1)} (${r.count})` : "–"}</span>
                    <span className="perf-score">
                      <span className="score-bar"><span style={{ width: `${score}%` }} /></span>
                      {score}
                    </span>
                  </div>
                );
              })}
            </div>
          </section>

          {/* Property list, map and details */}
          <div className="dash-grid">
            <div className="dash-panel">
              <div className="inline" style={{ justifyContent: "space-between", marginBottom: 12 }}>
                <strong>Property list</strong>
                <span className="muted">{filtered.length} shown</span>
              </div>
              <input
                className="dash-search"
                value={q}
                onChange={(e) => setQ(e.target.value)}
                placeholder="Search your property"
                aria-label="Search your property"
              />
              <div className="dash-chips">
                {FILTERS.map((f) => (
                  <button
                    key={f.value}
                    className={`chip ${filter === f.value ? "active" : ""}`}
                    onClick={() => setFilter(f.value)}
                  >
                    {f.label}
                  </button>
                ))}
              </div>

              {filtered.length ? (
                filtered.map((l) => {
                  const { avg, count } = ratingFor(reviews, l.id);
                  const isSel = selected?.id === l.id;
                  return (
                    <button
                      key={l.id}
                      className={`dash-item ${isSel ? "selected" : ""}`}
                      onClick={() => setSelectedId(l.id)}
                    >
                      <div className="dash-thumb">{CATEGORY_ICON[l.category]}</div>
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <div className="muted" style={{ fontSize: 12 }}>{l.category} · {l.purpose}</div>
                        <strong style={{ display: "block", fontSize: 14 }}>{l.title}</strong>
                        <div className="muted" style={{ fontSize: 12 }}>
                          ♡ {savesFor(l.id)} saved · {enquiriesFor(l.id)} enquiries · {count ? `★ ${avg.toFixed(1)}` : "No reviews"}
                        </div>
                        <div className="dash-bar">
                          <div style={{ width: `${count ? (avg / 5) * 100 : 0}%` }} />
                        </div>
                      </div>
                    </button>
                  );
                })
              ) : (
                <p className="muted" style={{ padding: "16px 0" }}>No properties match.</p>
              )}
            </div>

            <div className="dash-map-wrap">
              <MapView listings={filtered} />

              {selected && (
                <div className="dash-panel">
                  <div className="dash-detail-photo">{CATEGORY_ICON[selected.category]}</div>
                  <div className="inline" style={{ justifyContent: "space-between", marginTop: 14 }}>
                    <div>
                      <h2 style={{ fontSize: 24 }}>{selected.title}</h2>
                      <p className="muted">{selected.district}, Malawi</p>
                    </div>
                    <strong style={{ color: "var(--brand)" }}>{priceText(selected)}</strong>
                  </div>

                  <div className="dash-facts">
                    {selected.category !== "Land" ? (
                      <>
                        <div className="dash-fact">Bedrooms<strong>{selected.beds}</strong></div>
                        <div className="dash-fact">Bathrooms<strong>{selected.baths}</strong></div>
                      </>
                    ) : (
                      <div className="dash-fact">Type<strong>Land</strong></div>
                    )}
                    <div className="dash-fact">Area<strong>{selected.area.toLocaleString()} m²</strong></div>
                  </div>

                  <p className="muted" style={{ marginTop: 10, fontSize: 13 }}>
                    {specsText(selected)} · {isPromoted(selected) ? "⭐ Promoted" : "Not promoted"}
                  </p>

                  <div className="inline" style={{ marginTop: 14 }}>
                    <button className="btn btn-small" onClick={() => promote(selected.id, 7)}>⭐ Promote 7 days</button>
                    <Link className="btn btn-light btn-small" href={`/listing/${selected.id}`}>View listing</Link>
                    <Link className="btn btn-light btn-small" href={`/post?id=${selected.id}`}>Edit</Link>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Chat with people who messaged about my listings */}
          <section style={{ marginTop: 18 }}>
            <h2 className="sec-head" style={{ marginTop: 0 }}>Enquiries and chat</h2>
            {convos.length ? (
              <div className="chat">
                <div className="convos">
                  {convos.map((c) => {
                    const l = listings.find((x) => x.id === c.listingId);
                    const isActive = activeChat?.key === c.key;
                    return (
                      <button
                        key={c.key}
                        className={`convo ${isActive ? "active" : ""}`}
                        onClick={() => setChatKey(c.key)}
                      >
                        <strong>{nameOf(c.otherId)}</strong>
                        <span>{l ? l.title : "Listing removed"}</span>
                        <span>{c.last.text.slice(0, 40)}</span>
                      </button>
                    );
                  })}
                </div>

                {activeChat && (
                  <div className="thread">
                    <div className="thread-head">
                      <div>
                        <strong>{nameOf(activeChat.otherId)}</strong>
                        <div className="muted">
                          About: {listings.find((x) => x.id === activeChat.listingId)?.title ?? "Listing removed"}
                        </div>
                      </div>
                      <Link className="btn btn-light btn-small" href={`/listing/${activeChat.listingId}`}>View listing</Link>
                    </div>

                    <div className="msgs">
                      {thread.map((m) => (
                        <div key={m.id} className={`bubble ${m.from === meId ? "me" : "them"}`}>
                          {m.text}
                        </div>
                      ))}
                    </div>

                    <div className="compose">
                      <input
                        value={text}
                        onChange={(e) => setText(e.target.value)}
                        onKeyDown={(e) => e.key === "Enter" && sendReply()}
                        placeholder="Reply to this enquiry…"
                      />
                      <button className="btn btn-small" onClick={sendReply}>Send</button>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="empty">
                <div className="big">💬</div>
                <p>No enquiries yet. When someone messages you about a listing, the chat appears here.</p>
              </div>
            )}
          </section>
        </>
      )}
    </>
  );
}