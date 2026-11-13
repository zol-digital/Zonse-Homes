import Link from "next/link";

export default function Header() {
  return (
    <header className="border-b border-gray-200 bg-white">
      <nav className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        <Link href="/" className="text-xl font-bold text-green-700">
          Zonse Homes
        </Link>
        <div className="flex gap-6 text-sm font-medium text-gray-700">
          <Link href="/search" className="hover:text-green-700">Search</Link>
          <Link href="/advertisers/zol-digital" className="hover:text-green-700">Advertisers</Link>
          <Link href="/help" className="hover:text-green-700">Help</Link>
        </div>
      </nav>
    </header>
  );
}