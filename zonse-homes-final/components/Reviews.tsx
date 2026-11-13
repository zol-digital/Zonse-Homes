"use client";

import Link from "next/link";
import { useState } from "react";
import { ratingFor, useStore } from "@/lib/store";

export function Stars({ value }: { value: number }) {
  const full = Math.round(value);
  return (
    <span className="stars" aria-label={`${value.toFixed(1)} out of 5 stars`}>
      {"★".repeat(full)}
      {"☆".repeat(5 - full)}
    </span>
  );
}

export function Reviews({ listingId, ownerId }: { listingId: string; ownerId: string }) {
  const { me, reviews, addReview } = useStore();
  const [rating, setRating] = useState(5);
  const [text, setText] = useState("");
  const [error, setError] = useState("");
  const [done, setDone] = useState(false);

  const list = reviews.filter((r) => r.listingId === listingId);
  const { avg, count } = ratingFor(reviews, listingId);
  const alreadyReviewed = !!me && list.some((r) => r.authorId === me.id);
  const isOwner = !!me && me.id === ownerId;

  function submit() {
    const err = addReview(listingId, rating, text);
    if (err) {
      setError(err);
      return;
    }
    setError("");
    setText("");
    setRating(5);
    setDone(true);
    setTimeout(() => setDone(false), 2500);
  }

  return (
    <section className="reviews">
      <div className="reviews-head">
        <h2 className="sec-head" style={{ margin: 0 }}>Reviews</h2>
        {count > 0 ? (
          <span className="muted">
            <Stars value={avg} /> {avg.toFixed(1)} · {count} {count === 1 ? "review" : "reviews"}
          </span>
        ) : (
          <span className="muted">No reviews yet</span>
        )}
      </div>

      <div className="card review-form">
        {!me ? (
          <p className="muted">
            <Link href="/account">Log in</Link> to leave a review.
          </p>
        ) : isOwner ? (
          <p className="muted">You cannot review your own listing.</p>
        ) : alreadyReviewed ? (
          <p className="muted">You have already reviewed this listing. Thank you!</p>
        ) : (
          <>
            <p style={{ marginBottom: 8 }}>How was your stay?</p>
            <div className="star-pick" role="radiogroup" aria-label="Rating">
              {[1, 2, 3, 4, 5].map((n) => (
                <button
                  key={n}
                  type="button"
                  role="radio"
                  aria-checked={rating === n}
                  className={`star-btn ${n <= rating ? "on" : ""}`}
                  onClick={() => setRating(n)}
                >
                  ★
                </button>
              ))}
            </div>
            <textarea
              className="textarea"
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Tell others about the place, the host and the area…"
              style={{ marginTop: 12 }}
            />
            {error && <p style={{ color: "var(--danger)", fontSize: 13, marginTop: 8 }}>{error}</p>}
            <div className="inline" style={{ marginTop: 12 }}>
              <button className="btn btn-small" onClick={submit}>Post review</button>
              {done && <span className="muted">Thanks for your review ✓</span>}
            </div>
          </>
        )}
      </div>

      <div className="stack" style={{ marginTop: 16 }}>
        {list.map((r) => (
          <div key={r.id} className="card review-card">
            <div className="inline" style={{ justifyContent: "space-between" }}>
              <strong>{r.authorName}</strong>
              <span className="muted">{new Date(r.time).toLocaleDateString()}</span>
            </div>
            <div className="stars" style={{ margin: "4px 0 8px" }}>
              {"★".repeat(r.rating)}
              {"☆".repeat(5 - r.rating)}
            </div>
            <p className="muted" style={{ fontSize: 14, lineHeight: 1.6 }}>{r.text}</p>
          </div>
        ))}
      </div>
    </section>
  );
}