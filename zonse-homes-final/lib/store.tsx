"use client";

import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { seedData, type Data, type Listing, type User } from "@/lib/data";

type Theme = "light" | "dark";
type ListingInput = Omit<Listing, "id" | "owner" | "promoted" | "created">;

export type Review = {
  id: string;
  listingId: string;
  authorId: string;
  authorName: string;
  rating: number;
  text: string;
  time: number;
};

type Store = Data & {
  ready: boolean;
  me: User | null;
  theme: Theme;
  reviews: Review[];
  setTheme: (t: Theme) => void;
  toggleTheme: () => void;
  login: (email: string, password: string) => boolean;
  signup: (
    name: string,
    email: string,
    phone: string,
    password: string,
    accountType: User["accountType"],
    regNumber: string
  ) => string | null;
  verifyCompany: (userId: string) => void;
  logout: () => void;
  updateProfile: (name: string, phone: string) => void;
  toggleFav: (listingId: string) => boolean;
  saveListing: (input: ListingInput, id?: string) => string | null;
  deleteListing: (id: string) => void;
  promote: (id: string, days: number) => void;
  sendMessage: (listingId: string, otherId: string, text: string) => void;
  addReview: (listingId: string, rating: number, text: string) => string | null;
};

const DATA_KEY = "zonse-homes-v1";
const REVIEW_KEY = "zonse-reviews-v1";
const SESSION_KEY = "zh-session";
const THEME_KEY = "zh-theme";

const uid = () => Date.now().toString(36) + Math.random().toString(36).slice(2, 7);

// Fixed times so the server and browser render the same demo reviews
const BASE_MS = 1767225600000;
const DAY_MS = 864e5;

const seedReviews: Review[] = [
  { id: "r1", listingId: "l3", authorId: "guest-1", authorName: "Thoko M.", rating: 5, text: "Lovely cottage. Very clean, and the lake view is beautiful.", time: BASE_MS - 5 * DAY_MS },
  { id: "r2", listingId: "l3", authorId: "guest-2", authorName: "Chimwemwe K.", rating: 4, text: "Good location and the Wi-Fi worked well. Parking was a little tight.", time: BASE_MS - 9 * DAY_MS },
  { id: "r3", listingId: "l1", authorId: "guest-3", authorName: "Grace N.", rating: 4, text: "Secure and close to town. Water was reliable.", time: BASE_MS - 3 * DAY_MS },
];

export function ratingFor(reviews: Review[], listingId: string) {
  const mine = reviews.filter((r) => r.listingId === listingId);
  if (!mine.length) return { avg: 0, count: 0 };
  const total = mine.reduce((sum, r) => sum + r.rating, 0);
  return { avg: total / mine.length, count: mine.length };
}

const StoreContext = createContext<Store | null>(null);

export function StoreProvider({ children }: { children: ReactNode }) {
  const [data, setData] = useState<Data>(seedData);
  const [reviews, setReviews] = useState<Review[]>(seedReviews);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [theme, setThemeState] = useState<Theme>("light");
  const [ready, setReady] = useState(false);

  useEffect(() => {
    try {
      const raw = localStorage.getItem(DATA_KEY);
      if (raw) setData(JSON.parse(raw));
    } catch {}
    try {
      const rawReviews = localStorage.getItem(REVIEW_KEY);
      if (rawReviews) setReviews(JSON.parse(rawReviews));
    } catch {}
    setSessionId(localStorage.getItem(SESSION_KEY));
    const saved = localStorage.getItem(THEME_KEY) as Theme | null;
    setThemeState(
      saved ?? (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light")
    );
    setReady(true);
  }, []);

  useEffect(() => {
    if (!ready) return;
    try {
      localStorage.setItem(DATA_KEY, JSON.stringify(data));
    } catch {}
  }, [data, ready]);

  useEffect(() => {
    if (!ready) return;
    try {
      localStorage.setItem(REVIEW_KEY, JSON.stringify(reviews));
    } catch {}
  }, [reviews, ready]);

  useEffect(() => {
    document.body.classList.toggle("dark", theme === "dark");
  }, [theme]);

  const me = data.users.find((u) => u.id === sessionId) ?? null;

  function setSession(id: string | null) {
    setSessionId(id);
    if (id) localStorage.setItem(SESSION_KEY, id);
    else localStorage.removeItem(SESSION_KEY);
  }

  function setTheme(t: Theme) {
    setThemeState(t);
    localStorage.setItem(THEME_KEY, t);
  }

  function login(email: string, password: string) {
    const u = data.users.find(
      (x) => x.email === email.trim().toLowerCase() && x.password === password
    );
    if (!u) return false;
    setSession(u.id);
    return true;
  }

  function signup(
    name: string,
    email: string,
    phone: string,
    password: string,
    accountType: User["accountType"],
    regNumber: string
  ) {
    const clean = email.trim().toLowerCase();
    if (!name.trim() || !clean.includes("@")) return "Enter your name and a valid email";
    if (password.length < 6) return "Password must be at least 6 characters";
    if (data.users.some((u) => u.email === clean)) return "An account with this email already exists";
    if (accountType === "Company" && !regNumber.trim()) return "Companies must enter a registration number";
    const user: User = {
      id: uid(),
      name: name.trim(),
      email: clean,
      password,
      phone: phone.trim(),
      accountType,
      verified: false,
      regNumber: accountType === "Company" ? regNumber.trim() : "",
      favorites: [],
    };
    setData((d) => ({ ...d, users: [...d.users, user] }));
    setSession(user.id);
    return null;
  }

  function verifyCompany(userId: string) {
    setData((d) => ({
      ...d,
      users: d.users.map((u) => (u.id === userId ? { ...u, verified: true } : u)),
    }));
  }

  function logout() {
    setSession(null);
  }

  function updateProfile(name: string, phone: string) {
    if (!me) return;
    const id = me.id;
    setData((d) => ({
      ...d,
      users: d.users.map((u) => (u.id === id ? { ...u, name, phone } : u)),
    }));
  }

  function toggleFav(listingId: string) {
    if (!me) return false;
    const id = me.id;
    setData((d) => ({
      ...d,
      users: d.users.map((u) => {
        if (u.id !== id) return u;
        const has = u.favorites.includes(listingId);
        return {
          ...u,
          favorites: has
            ? u.favorites.filter((x) => x !== listingId)
            : [...u.favorites, listingId],
        };
      }),
    }));
    return true;
  }

  function saveListing(input: ListingInput, id?: string) {
    if (!me) return null;
    if (id) {
      setData((d) => ({
        ...d,
        listings: d.listings.map((l) => (l.id === id ? { ...l, ...input } : l)),
      }));
      return id;
    }
    const newId = uid();
    const owner = me.id;
    setData((d) => ({
      ...d,
      listings: [{ ...input, id: newId, owner, promoted: 0, created: Date.now() }, ...d.listings],
    }));
    return newId;
  }

  function deleteListing(id: string) {
    setData((d) => ({ ...d, listings: d.listings.filter((l) => l.id !== id) }));
  }

  function promote(id: string, days: number) {
    setData((d) => ({
      ...d,
      listings: d.listings.map((l) =>
        l.id !== id
          ? l
          : { ...l, promoted: Math.max(Date.now(), l.promoted) + days * 864e5 }
      ),
    }));
  }

  function sendMessage(listingId: string, otherId: string, text: string) {
    if (!me || !text.trim()) return;
    const from = me.id;
    setData((d) => ({
      ...d,
      messages: [
        ...d.messages,
        { id: uid(), listingId, from, to: otherId, text: text.trim(), time: Date.now() },
      ],
    }));
  }

  function addReview(listingId: string, rating: number, text: string) {
    if (!me) return "Log in to leave a review";
    const listing = data.listings.find((l) => l.id === listingId);
    if (!listing) return "This listing no longer exists";
    if (listing.owner === me.id) return "You cannot review your own listing";
    if (reviews.some((r) => r.listingId === listingId && r.authorId === me.id)) {
      return "You have already reviewed this listing";
    }
    if (!text.trim()) return "Please write a few words about your experience";
    const review: Review = {
      id: uid(),
      listingId,
      authorId: me.id,
      authorName: me.name,
      rating: Math.min(5, Math.max(1, Math.round(rating))),
      text: text.trim(),
      time: Date.now(),
    };
    setReviews((rs) => [review, ...rs]);
    return null;
  }

  const value: Store = {
    ...data,
    ready,
    me,
    theme,
    reviews,
    setTheme,
    toggleTheme: () => setTheme(theme === "dark" ? "light" : "dark"),
    login,
    signup,
    verifyCompany,
    logout,
    updateProfile,
    toggleFav,
    saveListing,
    deleteListing,
    promote,
    sendMessage,
    addReview,
  };

  return <StoreContext.Provider value={value}>{children}</StoreContext.Provider>;
}

export function useStore() {
  const ctx = useContext(StoreContext);
  if (!ctx) throw new Error("useStore must be used inside StoreProvider");
  return ctx;
}