"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";
import { ListingCard } from "@/components/ListingCard";
import { ADS, isPromoted } from "@/lib/data";
import { useLang } from "@/lib/language";
import { useStore } from "@/lib/store";

const SEARCH_ICON = (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <circle cx="11" cy="11" r="7" />
    <path d="m20 20-4-4" />
  </svg>
);

const MAP_ICON = (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.9} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d="M9 4 3 6v14l6-2 6 2 6-2V4l-6 2z" />
    <path d="M9 4v14M15 6v14" />
  </svg>
);

function AdCard({ k, onHide, label, hideLabel }: { k: number; onHide: () => void; label: string; hideLabel: string }) {
  const ad = ADS[(k - 1) % ADS.length];
  return (
    <article className="listing ad-card">
      <div className="cover ad-cover">
        <span className="tag">{label}</span>
        <div className="ad-mark">{ad.title}</div>
      </div>
      <div className="listing-body">
        <p className="muted">{ad.text}</p>
      </div>
      <button className="ad-x" onClick={onHide} aria-label={hideLabel}>
        ✕
      </button>
    </article>
  );
}

export default function HomePage() {
  const { listings } = useStore();
  const { t } = useLang();
  const router = useRouter();
  const [q, setQ] = useState("");
  const [hiddenAds, setHiddenAds] = useState<number[]>([]);

  const promoted = listings.filter((l) => isPromoted(l));
  const recent = [...listings].sort((a, b) => b.created - a.created);

  function search(e: FormEvent) {
    e.preventDefault();
    router.push(`/explore?q=${encodeURIComponent(q.trim())}`);
  }

  return (
    <>
      <section className="home-hero">
        <form className="home-search" onSubmit={search}>
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder={t("home.search")}
            aria-label={t("home.search")}
          />
          <button type="submit" className="search-go" aria-label={t("home.search")}>
            {SEARCH_ICON}
          </button>
        </form>
        <div className="home-actions">
          <Link href="/explore" className="icon-pill" title={t("home.explore")} aria-label={t("home.explore")}>
            {MAP_ICON}
          </Link>
        </div>
      </section>

      <section>
        <h2 className="big">{t("home.promoted")}</h2>
        {promoted.length ? (
          <div className="grid">
            {promoted.map((l, i) => (
              <ListingCard key={l.id} listing={l} index={i} />
            ))}
          </div>
        ) : (
          <p className="muted">{t("home.noPromoted")}</p>
        )}
      </section>

      <section>
        <h2 className="big">{t("home.all")}</h2>
        <div className="grid">
          {recent.flatMap((l, i) => {
            const items = [<ListingCard key={l.id} listing={l} index={i} />];
            const k = (i + 1) / 5;
            if ((i + 1) % 5 === 0 && !hiddenAds.includes(k)) {
              items.push(
                <AdCard
                  key={`ad-${k}`}
                  k={k}
                  onHide={() => setHiddenAds((h) => [...h, k])}
                  label={t("home.sponsored")}
                  hideLabel={t("home.hideAd")}
                />
              );
            }
            return items;
          })}
        </div>
      </section>
    </>
  );
}