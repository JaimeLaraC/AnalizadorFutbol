"use client";

import { Bell, Search, User, Sun, Moon } from "lucide-react";
import { usePathname } from "next/navigation";
import { useTheme } from "@/components/theme-provider";
import { cn } from "@/lib/utils";

export function Header() {
    const pathname = usePathname();
    const { theme, setTheme } = useTheme();

    const getGreeting = () => {
        const hour = new Date().getHours();
        if (hour < 12) return "Buenos días";
        if (hour < 18) return "Buenas tardes";
        return "Buenas noches";
    };

    const getPageTitle = () => {
        if (pathname === "/") return "Panel de Control";
        if (pathname.includes("predictions")) return "Predicciones";
        if (pathname.includes("stats")) return "Estadísticas";
        if (pathname.includes("database")) return "Explorador de Datos";
        return "Dashboard";
    };

    return (
        <header className="flex items-center justify-between mb-8 pt-2">
            <div>
                <h1 className="text-3xl font-bold text-foreground tracking-tight mb-1 transition-colors">
                    {getPageTitle()}
                </h1>
                <p className="text-sidebar-muted text-sm font-medium">
                    {getGreeting()}, Bienvenido al sistema.
                </p>
            </div>

            <div className="flex items-center gap-4">
                {/* Theme Toggle */}
                <button
                    onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
                    className="p-2.5 rounded-xl border border-card-border bg-card text-card-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground transition-all duration-300 relative group overflow-hidden"
                >
                    <div className="relative z-10">
                        {theme === "dark" ? (
                            <Moon className="w-5 h-5 transition-transform group-hover:-rotate-12" />
                        ) : (
                            <Sun className="w-5 h-5 transition-transform group-hover:rotate-45" />
                        )}
                    </div>
                </button>

                {/* Search Bar */}
                <div className="relative group hidden md:block">
                    <Search className="w-4 h-4 text-sidebar-muted absolute left-4 top-1/2 -translate-y-1/2 group-focus-within:text-sidebar-accent transition-colors" />
                    <input
                        type="text"
                        placeholder="Buscar..."
                        className="pl-11 pr-4 py-2.5 bg-card rounded-2xl border border-card-border text-sm text-foreground focus:outline-none focus:ring-1 focus:ring-sidebar-accent/50 focus:border-sidebar-accent/50 transition-all w-64 placeholder:text-sidebar-muted/50"
                    />
                </div>

                {/* Notifications */}
                <button className="relative p-2.5 bg-card rounded-xl border border-card-border hover:bg-card-foreground/5 transition-colors group">
                    <Bell className="w-5 h-5 text-sidebar-muted group-hover:text-foreground transition-colors" />
                    <span className="absolute top-2.5 right-3 w-2 h-2 bg-sidebar-accent rounded-full shadow-glow animate-pulse"></span>
                </button>

                {/* User Profile */}
                <div className="flex items-center gap-3 pl-4 border-l border-card-border">
                    <div className="text-right hidden md:block">
                        <p className="text-sm font-bold text-foreground">Admin User</p>
                        <p className="text-xs text-sidebar-muted">Pro Plan</p>
                    </div>
                    <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-sidebar-accent to-green-400 p-[1px] shadow-glow relative group cursor-pointer">
                        <div className="w-full h-full rounded-[11px] bg-card flex items-center justify-center overflow-hidden relative">
                            <User className="w-5 h-5 text-sidebar-accent relative z-10" />
                            <div className="absolute inset-0 bg-sidebar-accent/10 opacity-0 group-hover:opacity-100 transition-opacity" />
                        </div>
                    </div>
                </div>
            </div>
        </header>
    );
}
