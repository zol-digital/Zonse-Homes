import Link from "next/link";
import { typeLabel, type Property } from "@/lib/mock/properties";

function Heart({ saved }: { saved: boolean }) {
  return (
    <span className="absolute right-3 top-3 flex h-8 w-8 items-center justify-center rounded-full bg-white text-lg text-orange-500 shadow">
      {saved ? "♥" : "♡"}
    </span>
  );
}

export function PropertyCard({ property }: { property: Property }) {
  return (
    <Link href={`/properties/${property.slug}`} className="block w-60 shrink-0">
      <div className="relative h-36 rounded-2xl bg-gray-200">
        <Heart saved={property.saved} />
      </div>
      <p className="mt-3 text-xs text-gray-500">{typeLabel(property.type)}</p>
      <p className="font-semibold text-gray-900">{property.title}</p>
      <p className="text-xs text-gray-500">{property.location}</p>
      <p className="mt-1 text-sm font-bold text-gray-900">
        {property.price}{" "}
        {property.unit && <span className="font-normal text-gray-500">{property.unit}</span>}
      </p>
    </Link>
  );
}

export function PropertyRow({ property }: { property: Property }) {
  return (
    <Link
      href={`/properties/${property.slug}`}
      className="flex gap-4 border-b border-gray-100 py-4"
    >
      <div className="h-20 w-24 shrink-0 rounded-xl bg-gray-200" />
      <div className="min-w-0">
        <p className="text-xs text-gray-500">{typeLabel(property.type)}</p>
        <p className="truncate font-semibold text-gray-900">{property.title}</p>
        <p className="truncate text-xs text-gray-500">{property.location}</p>
        <p className="mt-1 text-sm font-bold text-gray-900">
          {property.price}{" "}
          {property.unit && <span className="font-normal text-gray-500">{property.unit}</span>}
        </p>
      </div>
    </Link>
  );
}