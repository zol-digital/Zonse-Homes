import Link from "next/link";
import { categories, type Category } from "@/lib/mock/properties";

export function CategoryTabs({ active }: { active: Category }) {
  return (
    <div className="flex justify-between gap-2 overflow-x-auto">
      {categories.map((c) => (
        <Link
          key={c.value}
          href={c.value === "all" ? "/search" : `/search?type=${c.value}`}
          className={`rounded-xl px-3 py-2 text-xs whitespace-nowrap ${
            active === c.value ? "bg-black font-semibold text-white" : "text-gray-600"
          }`}
        >
          {c.label}
        </Link>
      ))}
    </div>
  );
}