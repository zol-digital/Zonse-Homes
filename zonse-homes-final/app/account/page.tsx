"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { VerifiedBadge } from "@/components/VerifiedBadge";
import { useStore } from "@/lib/store";

function initials(name: string) {
  return name.split(" ").map((p) => p[0]).slice(0, 2).join("").toUpperCase();
}

export default function AccountPage() {
  const { me, listings, login, signup, logout, verifyCompany } = useStore();
  const router = useRouter();
  const [tab, setTab] = useState<"login" | "signup">("login");
  const [error, setError] = useState("");

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [name, setName] = useState("");
  const [sEmail, setSEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [sPass, setSPass] = useState("");
  const [type, setType] = useState<"Individual" | "Company">("Individual");
  const [regNo, setRegNo] = useState("");

  if (me) {
    const count = listings.filter((l) => l.owner === me.id).length;
    const isCompany = me.accountType === "Company";
    return (
      <div className="card" style={{ maxWidth: 560 }}>
        <div className="inline" style={{ marginBottom: 18 }}>
          <div className="avatar">{initials(me.name)}</div>
          <div>
            <h2 style={{ fontSize: 24 }}>{me.name}</h2>
            <p className="muted">{me.email} · {me.accountType}</p>
          </div>
        </div>

        {isCompany && (
          <div className="card" style={{ marginBottom: 18, padding: 16 }}>
            <strong>Company verification</strong>
            <p className="muted" style={{ margin: "6px 0 10px" }}>
              Registration number: {me.regNumber || "Not added"}
            </p>
            {me.verified ? (
              <VerifiedBadge />
            ) : (
              <>
                <p className="muted" style={{ marginBottom: 10 }}>
                  Your listings will show the verified badge once your company is verified.
                </p>
                <button className="btn btn-small" onClick={() => verifyCompany(me.id)}>
                  Demo: mark my company as verified
                </button>
                <p className="muted" style={{ fontSize: 12, marginTop: 8 }}>
                  Demo only. Replace this button with a real review before launch.
                </p>
              </>
            )}
          </div>
        )}

        <div className="stats">
          <div>Listings<strong>{count}</strong></div>
          <div>Saved<strong>{me.favorites.length}</strong></div>
          <div>Phone<strong>{me.phone || "Not added"}</strong></div>
        </div>
        <div className="inline" style={{ marginTop: 12 }}>
          <button className="btn" onClick={() => router.push("/post")}>+ New listing</button>
          <button className="btn btn-danger" onClick={() => { logout(); router.push("/explore"); }}>
            Log out
          </button>
        </div>
      </div>
    );
  }

  function onLogin() {
    if (!login(email, password)) return setError("Wrong email or password");
    setError("");
    router.push("/explore");
  }

  function onSignup() {
    const err = signup(name, sEmail, phone, sPass, type, regNo);
    if (err) return setError(err);
    setError("");
    router.push("/explore");
  }

  return (
    <div className="card" style={{ maxWidth: 520 }}>
      <div className="inline" style={{ marginBottom: 18 }}>
        <button className={`chip ${tab === "login" ? "active" : ""}`} onClick={() => setTab("login")}>
          Log in
        </button>
        <button className={`chip ${tab === "signup" ? "active" : ""}`} onClick={() => setTab("signup")}>
          Create account
        </button>
      </div>

      {tab === "login" ? (
        <>
          <div className="field">
            <label>Email</label>
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
          </div>
          <div className="field">
            <label>Password</label>
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
          </div>
          <button className="btn btn-full" onClick={onLogin}>Log in</button>
          <p className="muted" style={{ marginTop: 12 }}>Demo account: agent@demo.mw / demo123</p>
        </>
      ) : (
        <>
          <div className="field">
            <label>Full name</label>
            <input value={name} onChange={(e) => setName(e.target.value)} />
          </div>
          <div className="row2">
            <div className="field">
              <label>Email</label>
              <input type="email" value={sEmail} onChange={(e) => setSEmail(e.target.value)} />
            </div>
            <div className="field">
              <label>Phone</label>
              <input placeholder="+265..." value={phone} onChange={(e) => setPhone(e.target.value)} />
            </div>
          </div>
          <div className="row2">
            <div className="field">
              <label>I am a</label>
              <select className="select" value={type} onChange={(e) => setType(e.target.value as "Individual" | "Company")}>
                <option>Individual</option>
                <option>Company</option>
              </select>
            </div>
            <div className="field">
              <label>Password (min 6 characters)</label>
              <input type="password" value={sPass} onChange={(e) => setSPass(e.target.value)} />
            </div>
          </div>
          {type === "Company" && (
            <div className="field">
              <label>Company registration number</label>
              <input value={regNo} onChange={(e) => setRegNo(e.target.value)} placeholder="e.g. as shown on your certificate" />
              <p className="muted" style={{ fontSize: 12 }}>
                Companies are verified before the badge appears on their listings.
              </p>
            </div>
          )}
          <button className="btn btn-full" onClick={onSignup}>Create free account</button>
        </>
      )}

      {error && <p style={{ color: "var(--danger)", marginTop: 12, fontSize: 14 }}>{error}</p>}
    </div>
  );
}