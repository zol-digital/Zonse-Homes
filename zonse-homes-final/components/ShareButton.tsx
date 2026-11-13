"use client";

import { useState } from "react";

export function ShareButton({ title }: { title: string }) {
  const [msg, setMsg] = useState("");

  async function share() {
    const url = window.location.href;
    try {
      if (navigator.share) {
        await navigator.share({
          title,
          text: `Look at this place on Zonse Homes: ${title}`,
          url,
        });
        return;
      }
      await navigator.clipboard.writeText(url);
      setMsg("Link copied ✓");
    } catch (e) {
      // The user closed the share sheet on purpose, so say nothing
      if (e instanceof DOMException && e.name === "AbortError") return;
      setMsg("Could not share");
    }
    setTimeout(() => setMsg(""), 2000);
  }

  return (
    <button className="btn btn-light btn-full" onClick={share}>
      {msg || "🔗 Share listing"}
    </button>
  );
}