"use client";

import Link from "next/link";
import { ListingCard } from "@/components/ListingCard";
import { useStore } from "@/lib/store";

export default function SavedPage() {
  const { me, listings } = useStore();

  if (!me) {
    return (
      <div className="empty">
        <div className="big">♡</div>
        <p>Log in to see the listings you saved.</p>
        <br />
        <Link className="btn" href="/account">Log in</Link>
      </div>
    );
  }

  const saved = listings.filter((l) => me.favorites.includes(l.id));

  if (!saved.length) {
    return (
      <div className="empty">
        <div className="big">♡</div>
        <p>Tap the heart on any listing to save it here.</p>
        <br />
        <Link className="btn" href="/explore">Browse listings</Link>
      </div>
    );
  }

  return (
    <>
      <h1 style={{ fontSize: "clamp(2rem, 4vw, 3rem)", marginBottom: 6 }}>Saved</h1>
      <p className="muted" style={{ marginBottom: 18 }}>{saved.length} saved</p>
      <div className="grid">
        {saved.map((l, i) => (
          <ListingCard key={l.id} listing={l} index={i} />
        ))}
      </div>
    </>
  );
}