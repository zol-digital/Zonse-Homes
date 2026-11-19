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

// Replace these with your real social media addresses
const SOCIALS = [
  { label: "Facebook", href: "https://facebook.com/zonsehomes", path: "M14 8V6c0-1 .5-1.5 1.5-1.5H17V1h-2.5C11.8 1 11 3 11 5.5V8H8v3.5h3V23h3V11.5h2.7L17.5 8z" },
  { label: "X", href: "https://x.com/zonsehomes", path: "M18.2 2h3.4l-7.4 8.5L23 22h-6.8l-5.3-7-6.1 7H1.4l7.9-9L1 2h7l4.8 6.4L18.2 2zm-1.2 18h1.9L7.1 3.9H5.1L17 20z" },
  { label: "Instagram", href: "https://instagram.com/zonsehomes", path: "M12 2.2c3.2 0 3.6 0 4.8.1 3.2.1 4.8 1.7 4.9 4.9.1 1.3.1 1.6.1 4.8s0 3.6-.1 4.8c-.1 3.2-1.7 4.8-4.9 4.9-1.3.1-1.6.1-4.8.1s-3.6 0-4.8-.1c-3.3-.1-4.8-1.7-4.9-4.9C2.2 15.6 2.2 15.2 2.2 12s0-3.6.1-4.8C2.4 3.9 3.9 2.4 7.2 2.3 8.4 2.2 8.8 2.2 12 2.2zM12 0C8.7 0 8.3 0 7.1.1 2.7.3.3 2.7.1 7.1 0 8.3 0 8.7 0 12s0 3.7.1 4.9c.2 4.4 2.6 6.8 7 7 1.2.1 1.6.1 4.9.1s3.7 0 4.9-.1c4.4-.2 6.8-2.6 7-7 .1-1.2.1-1.6.1-4.9s0-3.7-.1-4.9c-.2-4.4-2.6-6.8-7-7C15.7 0 15.3 0 12 0zm0 5.8a6.2 6.2 0 100 12.4 6.2 6.2 0 000-12.4zM12 16a4 4 0 110-8 4 4 0 010 8zm6.4-11.8a1.4 1.4 0 100 2.9 1.4 1.4 0 000-2.9z" },
];

export default function FaqPage() {
  const [open, setOpen] = useState<number | null>(null);

  return (
    <>
      <div className="card" style={{ marginBottom: 22 }}>
        <h2 style={{ fontSize: 28, marginBottom: 6 }}>How can we help?</h2>
        <p className="muted">
          Browse the most common questions below. Still stuck? Visit <Link href="/support">Customer support</Link>.
        </p>
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

      <footer className="help-footer">
        <div className="help-social">
          {SOCIALS.map((s) => (
            <a key={s.label} href={s.href} target="_blank" rel="noopener noreferrer" aria-label={s.label} className="help-social-link">
              <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                <path d={s.path} />
              </svg>
            </a>
          ))}
        </div>
        <p className="help-copy">© 2026 ZOL, Inc.</p>
      </footer>
    </>
  );
}
