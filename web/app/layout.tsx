import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Streaming Ops",
  description: "Streaming pipeline operations console",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ko">
      <body className="antialiased bg-gray-950 text-gray-100 min-h-screen">
        <nav className="border-b border-gray-800 px-4 py-3 flex gap-4">
          <a href="/" className="text-white hover:underline">Home</a>
          <a href="/channels" className="text-white hover:underline">Channels</a>
          <a href="/events" className="text-white hover:underline">Events</a>
        </nav>
        {children}
      </body>
    </html>
  );
}
