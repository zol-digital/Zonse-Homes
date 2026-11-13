"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { CATEGORY_ICON, isPromoted, priceText, specsText, tagText, type Listing } from "@/lib/data";
import { ratingFor, useStore } from "@/lib/store";
import { VerifiedBadge } from "@/components/VerifiedBadge";

export function ListingCard({ listing, index = 0 }: { listing: Listing; index?: number }) {
  const { me, users, reviews, toggleFav } = useStore();
  const router = useRouter();
  const saved = me?.favorites.includes(listing.id) ?? false;
  const promoted = isPromoted(listing);

  const owner = users.find((u) => u.id === listing.owner);
  const verified = owner?.accountType === "Company" && owner.verified;
  const { avg, count } = ratingFor(reviews, listing.id);

  function onFav() {
    if (!toggleFav(listing.id)) router.push("/account");
  }

  return (
    <article className="listing" style={{ animationDelay: `${Math.min(index, 10) * 60}ms` }}>
      <Link href={`/listing/${listing.id}`} className="listing-link">
        <div className="cover">
          <div className="emoji">{CATEGORY_ICON[listing.category]}</div>
          <span className={`tag ${promoted ? "promo-tag" : ""}`}>{tagText(listing)}</span>
        </div>
        <div className="listing-body">
          {verified && <div style={{ marginBottom: 6 }}><VerifiedBadge /></div>}
          <div className="muted">
            {listing.category} · {listing.district}
          </div>
          <h3>{listing.title}</h3>
          <div className="muted">{specsText(listing)}</div>
          {count > 0 && (
            <div className="muted">★ {avg.toFixed(1)} ({count})</div>
          )}
          <div className="price">{priceText(listing)}</div>
        </div>
      </Link>
      <button
        className={`fav ${saved ? "on" : ""}`}
        onClick={onFav}
        aria-label={saved ? "Remove from saved" : "Save listing"}
      >
        {saved ? "♥" : "♡"}
      </button>
    </article>
  );
}