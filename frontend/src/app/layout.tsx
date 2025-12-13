import type { Metadata } from "next";
import { Outfit } from "next/font/google";
import "./globals.css";
import { Sidebar } from "@/components/layout/Sidebar";
import { ThemeProvider } from "@/components/theme-provider";
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
    <html lang="es" suppressHydrationWarning>
      <body
        className={cn(
          outfit.variable,
          "antialiased min-h-screen"
        )}
      >
        <ThemeProvider defaultTheme="dark" storageKey="app-theme">
          <div className="flex min-h-screen">
            <Sidebar />
            <main className="flex-1 ml-4 lg:ml-72 transition-all duration-300 p-6">
              {children}
            </main>
          </div>
        </ThemeProvider>
      </body>
    </html>
  );
}
