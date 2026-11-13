import Link from "next/link";

export default function Footer() {
  return (
    <footer className="mt-16 border-t border-gray-200 bg-gray-50">
      <div className="mx-auto flex max-w-6xl flex-col gap-6 px-6 py-10 sm:flex-row sm:justify-between">
        <div>
          <p className="font-bold text-green-700">Zonse Homes</p>
          <p className="mt-2 max-w-sm text-sm text-gray-600">
            Property listings for Malawi. Listing details come from advertisers, so check important information yourself before you pay or sign.
          </p>
        </div>
        <div className="flex gap-6 text-sm text-gray-700">
          <Link href="/help" className="hover:text-green-700">Help and safety</Link>
          <Link href="/search" className="hover:text-green-700">Search</Link>
          <Link href="/advertisers/zol-digital" className="hover:text-green-700">Advertisers</Link>
        </div>
      </div>
    </footer>
  );
}