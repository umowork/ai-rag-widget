import type { Metadata } from "next";
import { Sidebar } from "./components/sidebar";
import "./globals.css";

export const metadata: Metadata = {
  title: "RAG Admin",
  description: "Admin panel for AI RAG Widget",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen antialiased">
        <div className="flex min-h-screen">
          <Sidebar />
          <main className="flex-1 overflow-auto">
            <div className="max-w-5xl mx-auto p-8">{children}</div>
          </main>
        </div>
      </body>
    </html>
  );
}
