"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const items = [
  { href: "/", label: "Home", icon: "⌂" },
  { href: "/search", label: "Explore", icon: "◎" },
  { href: "/saved", label: "Saved", icon: "♥" },
  { href: "/profile", label: "Profile", icon: "☺" },
];

export default function BottomNav() {
  const pathname = usePathname();

  return (
    <nav className="fixed bottom-0 left-1/2 z-40 flex h-16 w-full max-w-md -translate-x-1/2 items-center justify-around border-t border-gray-200 bg-white">
      {items.map((item) => {
        const active = item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);
        return (
          <Link
            key={item.href}
            href={item.href}
            className={`flex flex-col items-center text-xs ${
              active ? "font-semibold text-black" : "text-gray-400"
            }`}
          >
            <span className="text-lg">{item.icon}</span>
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}