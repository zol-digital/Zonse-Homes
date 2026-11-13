"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";
import { type Message } from "@/lib/data";
import { useStore } from "@/lib/store";

type Convo = { listingId: string; otherId: string; last: Message | null };

function MessagesInner() {
  const { me, listings, users, messages, sendMessage } = useStore();
  const params = useSearchParams();
  const [text, setText] = useState("");

  if (!me) {
    return (
      <div className="empty">
        <div className="big">💬</div>
        <p>Log in to see your messages.</p>
        <br />
        <Link className="btn" href="/account">Log in</Link>
      </div>
    );
  }

  // Build one conversation per listing and person
  const mine = messages.filter((m) => m.from === me.id || m.to === me.id);
  const map = new Map<string, Convo>();
  mine.forEach((m) => {
    const other = m.from === me.id ? m.to : m.from;
    const key = m.listingId + ":" + other;
    const prev = map.get(key);
    if (!prev || (prev.last && m.time > prev.last.time)) {
      map.set(key, { listingId: m.listingId, otherId: other, last: m });
    }
  });
  const convos = [...map.values()].sort((a, b) => (b.last?.time ?? 0) - (a.last?.time ?? 0));

  // Opening from "Message seller" selects that listing
  const requested = params.get("listing");
  let active: Convo | null = convos.find((c) => c.listingId === requested) ?? convos[0] ?? null;
  if (requested && !convos.some((c) => c.listingId === requested)) {
    const l = listings.find((x) => x.id === requested);
    if (l) active = { listingId: l.id, otherId: l.owner, last: null };
  }

  if (!active) {
    return (
      <div className="empty">
        <div className="big">💬</div>
        <p>No conversations yet. Open a listing and press <strong>Message seller</strong> to start chatting.</p>
        <br />
        <Link className="btn" href="/explore">Browse listings</Link>
      </div>
    );
  }

  const listing = listings.find((l) => l.id === active!.listingId);
  const other = users.find((u) => u.id === active!.otherId);
  const thread = messages
    .filter(
      (m) =>
        m.listingId === active!.listingId &&
        ((m.from === me.id && m.to === active!.otherId) ||
          (m.from === active!.otherId && m.to === me.id))
    )
    .sort((a, b) => a.time - b.time);

  const isOwnListing = active.otherId === me.id;

  function onSend() {
    if (!text.trim() || !active || isOwnListing) return;
    sendMessage(active.listingId, active.otherId, text);
    setText("");
  }

  return (
    <>
      <h1 style={{ fontSize: "clamp(2rem, 4vw, 3rem)", marginBottom: 6 }}>Messages</h1>
      <p className="muted" style={{ marginBottom: 18 }}>Chat with people interested in your listings</p>

      <div className="chat">
        <div className="convos">
          {convos.map((c) => {
            const l = listings.find((x) => x.id === c.listingId);
            const who = users.find((u) => u.id === c.otherId);
            const isActive = c.listingId === active!.listingId && c.otherId === active!.otherId;
            return (
              <Link
                key={c.listingId + c.otherId}
                href={`/messages?listing=${c.listingId}`}
                className={`convo ${isActive ? "active" : ""}`}
                style={{ display: "block", color: "inherit", textDecoration: "none" }}
              >
                <strong>{who ? who.name : "Member"}</strong>
                <span>{l ? l.title : "Listing removed"}</span>
                <span>{c.last ? c.last.text.slice(0, 40) : "New conversation"}</span>
              </Link>
            );
          })}
        </div>

        <div className="thread">
          <div className="thread-head">
            <div>
              <strong>{other ? other.name : "Member"}</strong>
              <div className="muted">About: {listing ? listing.title : "Listing removed"}</div>
            </div>
            {listing && <Link className="btn btn-light btn-small" href={`/listing/${listing.id}`}>View listing</Link>}
          </div>

          <div className="msgs">
            {thread.length ? (
              thread.map((m) => (
                <div key={m.id} className={`bubble ${m.from === me.id ? "me" : "them"}`}>{m.text}</div>
              ))
            ) : (
              <div className="muted" style={{ margin: "auto", textAlign: "center" }}>No messages yet. Say hello 👋</div>
            )}
          </div>

          {isOwnListing ? (
            <p className="muted" style={{ padding: 14 }}>This is your own listing, so there is no conversation with a seller.</p>
          ) : (
            <div className="compose">
              <input
                value={text}
                onChange={(e) => setText(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && onSend()}
                placeholder="Write a message…"
              />
              <button className="btn btn-small" onClick={onSend}>Send</button>
            </div>
          )}
        </div>
      </div>
    </>
  );
}

export default function MessagesPage() {
  return (
    <Suspense fallback={null}>
      <MessagesInner />
    </Suspense>
  );
}