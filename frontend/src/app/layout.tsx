import type { Metadata } from "next";
import { Outfit } from "next/font/google";
import "./globals.css";
import { Sidebar } from "@/components/layout/Sidebar";
import { cn } from "@/lib/utils";

const outfit = Outfit({
  subsets: ["latin"],
  variable: "--font-sans",
});

export const metadata: Metadata = {
  title: "AnalizadorFutbol - Dashboard AI",
  description: "Predicciones de fútbol basadas en IA",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="es">
      <body
        className={cn(
          outfit.variable,
          "antialiased min-h-screen pl-72 pr-6 py-6"
        )}
      >
        <Sidebar />
        <main className="min-h-[calc(100vh-3rem)]">
          {children}
        </main>
      </body>
    </html>
  );
}
