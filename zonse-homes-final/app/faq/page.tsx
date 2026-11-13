"use client";

import Link from "next/link";
import { useState } from "react";

const FAQS: [string, string][] = [
  ["Is Zonse Homes really free to use?", "Yes. Creating an account, posting listings, browsing, saving favourites and chatting are all free. There are no monthly subscriptions."],
  ["How do I post a house, apartment, Airbnb or land?", "Log in, press Post a Listing, fill in the details, choose your district and publish. Your listing appears on Explore straight away."],
  ["Can companies and individuals both post?", "Yes. When you sign up, choose Individual or Company. Both can post listings for rent, sale, short stays or land."],
  ["What does Promote mean?", "Promoting a listing puts it at the top of search results with a ⭐ badge for 7 or 30 days. It is optional. A normal listing stays free."],
  ["How do I contact a seller?", "Open a listing and press Message seller. You need to be logged in. Your conversation appears under Messages."],
  ["Are the ads intrusive?", "No. Ads are small, clearly marked as Sponsored, and appear only between listings. You can close any ad with the ✕ button."],
  ["How do I switch between light and dark mode?", "Press the 🌙 or ☀️ button at the top right, or use the Appearance options in Settings."],
];

export default function FaqPage() {
  const [open, setOpen] = useState<number | null>(null);

  return (
    <>
      <div className="card" style={{ marginBottom: 22 }}>
        <h2 style={{ fontSize: 28, marginBottom: 6 }}>How can we help?</h2>
        <p className="muted">Browse the most common questions below. Still stuck? Visit <Link href="/support">Customer support</Link>.</p>
      </div>

      <div className="card" style={{ maxWidth: 820, padding: "6px 22px" }}>
        {FAQS.map(([q, a], i) => (
          <div key={q} className="faq-item">
            <button className="faq-q" onClick={() => setOpen(open === i ? null : i)}>
              {q}
              <span className="plus" style={{ transform: open === i ? "rotate(45deg)" : "none" }}>+</span>
            </button>
            {open === i && <p className="faq-a">{a}</p>}
          </div>
        ))}
      </div>
    </>
  );
}