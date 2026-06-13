import Link from "next/link";

export default function NotFound() {
  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center px-4">
      <div className="text-center space-y-4">
        <h1 className="text-6xl font-bold text-[#9400D3]">404</h1>
        <h2 className="text-xl font-semibold text-white">Page not found</h2>
        <p className="text-gray-400 text-sm">
          The page you're looking for doesn't exist.
        </p>
        <Link
          href="/"
          className="inline-block bg-[#9400D3] hover:bg-[#7a00b0] transition text-white font-medium px-6 py-2.5 rounded-lg mt-2 text-sm"
        >
          Go home
        </Link>
      </div>
    </div>
  );
}