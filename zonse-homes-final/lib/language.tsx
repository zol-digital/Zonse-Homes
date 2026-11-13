"use client";

import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { DICT, type Key, type Lang } from "@/lib/i18n";

const LANG_KEY = "zh-lang";

type LangContextValue = {
  lang: Lang;
  setLang: (l: Lang) => void;
  t: (k: Key) => string;
};

const LangContext = createContext<LangContextValue | null>(null);

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Lang>("en");

  // Read the saved language after the page loads, so the server and browser match
  useEffect(() => {
    const saved = localStorage.getItem(LANG_KEY) as Lang | null;
    if (saved && saved in DICT) setLangState(saved);
  }, []);

  useEffect(() => {
    document.documentElement.lang = lang;
  }, [lang]);

  function setLang(l: Lang) {
    setLangState(l);
    localStorage.setItem(LANG_KEY, l);
  }

  const t = (k: Key) => DICT[lang][k] ?? DICT.en[k];

  return (
    <LangContext.Provider value={{ lang, setLang, t }}>
      {children}
    </LangContext.Provider>
  );
}

export function useLang() {
  const ctx = useContext(LangContext);
  if (!ctx) throw new Error("useLang must be used inside LanguageProvider");
  return ctx;
}