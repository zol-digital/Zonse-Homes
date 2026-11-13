"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, type ReactNode } from "react";
import { LANGUAGES, type Key } from "@/lib/i18n";
import { useLang } from "@/lib/language";
import { useStore } from "@/lib/store";

const MAIN_NAV: { href: string; key: Key }[] = [
  { href: "/", key: "nav.home" },
  { href: "/explore", key: "nav.explore" },
  { href: "/mine", key: "nav.mine" },
  { href: "/post", key: "nav.post" },
  { href: "/saved", key: "nav.saved" },
  { href: "/messages", key: "nav.messages" },
  { href: "/settings", key: "nav.settings" },
];

const HELP_NAV: { href: string; key: Key }[] = [
  { href: "/faq", key: "nav.faq" },
  { href: "/support", key: "nav.support" },
  { href: "/account", key: "nav.account" },
];

const icons = {
  home: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M3 10.5 12 3l9 7.5V20a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z" />
    </svg>
  ),
  compass: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <circle cx="12" cy="12" r="9" />
      <path d="m15.5 8.5-2 5-5 2 2-5z" />
    </svg>
  ),
  heart: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M12 20s-7-4.4-9.3-8.6C1.1 8.3 3 5 6.4 5c2 0 3.4 1.1 4.1 2.2h1C12.2 6.1 13.6 5 15.6 5 19 5 20.9 8.3 21.3 11.4 19 15.6 12 20 12 20z" />
    </svg>
  ),
  person: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <circle cx="12" cy="8" r="4" />
      <path d="M4 21c1.5-4 4.5-6 8-6s6.5 2 8 6" />
    </svg>
  ),
};

function isActive(pathname: string, href: string) {
  return href === "/" ? pathname === "/" : pathname.startsWith(href);
}

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const { me, theme, toggleTheme } = useStore();
  const { lang, setLang, t } = useLang();

  useEffect(() => {
    document.body.classList.remove("menu-open");
  }, [pathname]);

  const dock = [
    { href: "/", label: t("nav.home"), icon: icons.home, count: 0 },
    { href: "/explore", label: t("nav.explore"), icon: icons.compass, count: 0 },
    { href: "/saved", label: t("nav.saved"), icon: icons.heart, count: me?.favorites.length ?? 0 },
    { href: "/account", label: t("dock.profile"), icon: icons.person, count: 0 },
  ];

  return (
    <div className="app">
      <header className="app-bar">
        <button
          className="menu-btn"
          aria-label={t("nav.menu")}
          onClick={() => document.body.classList.toggle("menu-open")}
        >
          <span />
          <span />
          <span />
        </button>
        <div className="app-logo">
          <span>Zonse Homes</span>
        </div>
        <button
          className="icon-btn app-bar-spacer"
          onClick={toggleTheme}
          title={t("nav.theme")}
          aria-label={t("nav.theme")}
        >
          {theme === "dark" ? "☀️" : "🌙"}
        </button>
      </header>

      <aside className="sidebar">
        <nav className="nav">
          {MAIN_NAV.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={isActive(pathname, item.href) ? "active" : ""}
            >
              {t(item.key)}
            </Link>
          ))}
        </nav>
        <Link href="/dashboard" className={isActive(pathname, "/dashboard") ? "active" : ""}>Dashboard</Link>
        <div className="sidebar-bottom">
          <nav className="nav">
            {HELP_NAV.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={isActive(pathname, item.href) ? "active" : ""}
              >
                {t(item.key)}
              </Link>
            ))}
          </nav>
          <div className="lang-picker">
            <label htmlFor="lang-select">{t("settings.language")}</label>
            <select
              id="lang-select"
              className="select"
              value={lang}
              onChange={(e) => setLang(e.target.value as typeof lang)}
            >
              {LANGUAGES.map((l) => (
                <option key={l.code} value={l.code}>
                  {l.name}
                </option>
              ))}
            </select>
          </div>
          <div className="account-box">
            <strong>{me ? me.name : t("nav.guest")}</strong>
            <span>{me ? me.email : t("nav.guestHint")}</span>
          </div>
        </div>
      </aside>

      <main className="main">
        <section className="content">{children}</section>
      </main>

      <div
        className="menu-scrim"
        onClick={() => document.body.classList.remove("menu-open")}
      />

      <nav className="dock" aria-label="Main">
        {dock.map((item) => {
          const active = isActive(pathname, item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={active ? "active" : ""}
              aria-current={active ? "page" : undefined}
            >
              <span className="dock-icon">
                {item.icon}
                {item.count > 0 && <span className="dock-badge">{item.count}</span>}
              </span>
              <span className="dock-label">{item.label}</span>
            </Link>
          );
        })}
      </nav>
    </div>
  );
}