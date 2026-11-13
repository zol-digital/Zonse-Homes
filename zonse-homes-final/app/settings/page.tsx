"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { LANGUAGES } from "@/lib/i18n";
import { useLang } from "@/lib/language";
import { useStore } from "@/lib/store";

export default function SettingsPage() {
  const { me, theme, setTheme, updateProfile, logout } = useStore();
  const { lang, setLang, t } = useLang();
  const router = useRouter();
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (me) {
      setName(me.name);
      setPhone(me.phone);
    }
  }, [me]);

  return (
    <>
      <h1 style={{ fontSize: "clamp(2rem, 4vw, 3rem)", marginBottom: 6 }}>{t("settings.title")}</h1>
      <p className="muted" style={{ marginBottom: 18 }}>{t("settings.sub")}</p>

      <div style={{ maxWidth: 640 }}>
        <div className="card" style={{ marginBottom: 18 }}>
          <h3 className="sec-title">{t("settings.language")}</h3>
          <p className="muted" style={{ marginBottom: 14 }}>{t("settings.languageSub")}</p>
          <div className="inline">
            {LANGUAGES.map((l) => (
              <button
                key={l.code}
                className={`chip ${lang === l.code ? "active" : ""}`}
                onClick={() => setLang(l.code)}
              >
                {l.name}
              </button>
            ))}
          </div>
        </div>

        <div className="card" style={{ marginBottom: 18 }}>
          <h3 className="sec-title">{t("settings.appearance")}</h3>
          <p className="muted" style={{ marginBottom: 14 }}>{t("settings.appearanceSub")}</p>
          <div className="inline">
            <button className={`chip ${theme === "light" ? "active" : ""}`} onClick={() => setTheme("light")}>
              {t("settings.light")}
            </button>
            <button className={`chip ${theme === "dark" ? "active" : ""}`} onClick={() => setTheme("dark")}>
              {t("settings.dark")}
            </button>
          </div>
        </div>

        {me ? (
          <div className="card">
            <h3 className="sec-title">{t("settings.profile")}</h3>
            <div className="field">
              <label>{t("settings.name")}</label>
              <input value={name} onChange={(e) => setName(e.target.value)} />
            </div>
            <div className="field">
              <label>{t("settings.phone")}</label>
              <input value={phone} onChange={(e) => setPhone(e.target.value)} />
            </div>
            <div className="inline">
              <button
                className="btn"
                onClick={() => {
                  if (!name.trim()) return;
                  updateProfile(name.trim(), phone.trim());
                  setSaved(true);
                  setTimeout(() => setSaved(false), 2000);
                }}
              >
                {t("settings.save")}
              </button>
              <button
                className="btn btn-danger"
                onClick={() => {
                  logout();
                  router.push("/explore");
                }}
              >
                {t("settings.logout")}
              </button>
              {saved && <span className="muted">{t("settings.saved")}</span>}
            </div>
          </div>
        ) : (
          <div className="card">
            <p className="muted" style={{ marginBottom: 14 }}>{t("settings.loginPrompt")}</p>
            <button className="btn" onClick={() => router.push("/account")}>{t("settings.loginBtn")}</button>
          </div>
        )}
      </div>
    </>
  );
}