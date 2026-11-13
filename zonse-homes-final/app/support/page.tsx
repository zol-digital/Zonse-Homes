"use client";

import { useStore } from "@/lib/store";
import { useState } from "react";

const SUPPORT = {
  phone: "+265 999 000 000",
  whatsapp: "265999000000",
  email: "support@zonsehomes.mw",
  hours: "Mon–Sat, 8am–6pm",
};

export default function SupportPage() {
  const { me } = useStore();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [subject, setSubject] = useState("Listing help");
  const [message, setMessage] = useState("");
  const [status, setStatus] = useState<"" | "sent" | "error">("");

  function send() {
    if (!name.trim() || !email.trim() || !message.trim()) {
      setStatus("error");
      return;
    }
    // Demo mode: the message is not stored or emailed anywhere yet
    setStatus("sent");
    setMessage("");
  }

  return (
    <>
      <div className="card" style={{ marginBottom: 22 }}>
        <h2 style={{ fontSize: 28, marginBottom: 6 }}>We are here to help</h2>
        <p className="muted">Talk to a real person about a listing, a payment or your account. Hours: {SUPPORT.hours}.</p>
      </div>

      <div className="grid" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", marginBottom: 22 }}>
        <a className="card" href={`tel:${SUPPORT.phone.replace(/\s/g, "")}`} style={{ textDecoration: "none" }}>
          <div style={{ fontSize: 26 }}>📞</div>
          <strong>Call us</strong>
          <p className="muted">{SUPPORT.phone}</p>
        </a>
        <a className="card" href={`https://wa.me/${SUPPORT.whatsapp}`} target="_blank" rel="noopener noreferrer" style={{ textDecoration: "none" }}>
          <div style={{ fontSize: 26 }}>💬</div>
          <strong>WhatsApp</strong>
          <p className="muted">Quick replies</p>
        </a>
        <a className="card" href={`mailto:${SUPPORT.email}`} style={{ textDecoration: "none" }}>
          <div style={{ fontSize: 26 }}>✉️</div>
          <strong>Email</strong>
          <p className="muted">{SUPPORT.email}</p>
        </a>
      </div>

      <div className="card" style={{ maxWidth: 660 }}>
        <h3 className="sec-title">Send us a message</h3>
        <div className="row2">
          <div className="field">
            <label>Your name</label>
            <input value={name} onChange={(e) => setName(e.target.value)} defaultValue={me?.name} />
          </div>
          <div className="field">
            <label>Email</label>
            <input value={email} onChange={(e) => setEmail(e.target.value)} defaultValue={me?.email} />
          </div>
        </div>
        <div className="field">
          <label>Topic</label>
          <select className="select" value={subject} onChange={(e) => setSubject(e.target.value)}>
            <option>Listing help</option>
            <option>Payments and promotion</option>
            <option>Account problem</option>
            <option>Report a listing</option>
            <option>Something else</option>
          </select>
        </div>
        <div className="field">
          <label>Message</label>
          <textarea className="textarea" value={message} onChange={(e) => setMessage(e.target.value)} placeholder="Tell us what happened…" />
        </div>
        <button className="btn" onClick={send}>Send message</button>
        {status === "sent" && <p style={{ color: "var(--brand)", marginTop: 12 }}>Message sent. We reply within 24 hours 💚</p>}
        {status === "error" && <p style={{ color: "var(--danger)", marginTop: 12 }}>Please fill in your name, email and message.</p>}
      </div>
    </>
  );
}