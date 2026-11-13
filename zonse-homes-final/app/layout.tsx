import type { Metadata } from "next";
import { AppShell } from "@/components/AppShell";
import { LanguageProvider } from "@/lib/language";
import { StoreProvider } from "@/lib/store";
import "./globals.css";

// Render every page on request, so time-based checks such as promoted listings work

export const metadata: Metadata = {
  title: "Zonse Homes",
  description: "Find property in Malawi",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="" />
        <link
          href="https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=Inter:wght@400;500;600;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>
        <LanguageProvider>
          <StoreProvider>
            <AppShell>{children}</AppShell>
          </StoreProvider>
        </LanguageProvider>
      </body>
    </html>
  );
}