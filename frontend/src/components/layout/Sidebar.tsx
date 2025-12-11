"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
    LayoutDashboard,
    Trophy,
    BarChart2,
    Settings,
    RefreshCcw,
    Activity,
    Zap,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { motion } from "framer-motion";

const menuItems = [
    { icon: LayoutDashboard, label: "Dashboard", href: "/" },
    { icon: Zap, label: "Predicciones", href: "/predictions" },
    { icon: BarChart2, label: "Estadísticas", href: "/stats" },
    { icon: RefreshCcw, label: "Sincronización", href: "/sync" },
    { icon: Settings, label: "Configuración", href: "/settings" },
];

export function Sidebar() {
    const pathname = usePathname();

    return (
        <aside className="fixed left-4 top-4 bottom-4 w-64 bg-sidebar rounded-3xl flex flex-col p-6 shadow-2xl z-50">
            {/* Logo */}
            <div className="flex items-center gap-3 px-2 mb-10">
                <div className="p-2 bg-sidebar-foreground/10 rounded-full">
                    <Trophy className="w-6 h-6 text-sidebar-foreground" />
                </div>
                <span className="text-xl font-bold text-sidebar-foreground tracking-tight">
                    Analizador<span className="text-sidebar-accent">Futbol</span>
                </span>
            </div>

            {/* Menu */}
            <nav className="flex-1 space-y-2">
                {menuItems.map((item) => {
                    const isActive = pathname === item.href;

                    return (
                        <Link
                            key={item.href}
                            href={item.href}
                            className="relative block"
                        >
                            <div
                                className={cn(
                                    "flex items-center gap-3 px-4 py-3 rounded-2xl transition-all duration-200 group",
                                    isActive
                                        ? "text-sidebar bg-sidebar-accent font-semibold"
                                        : "text-sidebar-muted hover:text-sidebar-foreground hover:bg-sidebar-foreground/5"
                                )}
                            >
                                <item.icon className={cn("w-5 h-5", isActive ? "stroke-[2.5px]" : "stroke-2")} />
                                <span>{item.label}</span>
                            </div>
                        </Link>
                    );
                })}
            </nav>

            {/* Model Status Card */}
            <div className="bg-sidebar-accent rounded-2xl p-4 mt-auto relative overflow-hidden group">
                <div className="relative z-10">
                    <div className="flex items-center gap-2 mb-2">
                        <Activity className="w-5 h-5 text-sidebar stroke-[2.5px]" />
                        <span className="font-bold text-sidebar">Modelo V1.0</span>
                    </div>
                    <p className="text-sm text-sidebar/80 font-medium mb-3">
                        Precisión actual:
                        <br />
                        <span className="text-2xl font-bold text-black">78.5%</span>
                    </p>
                    <button className="bg-sidebar text-white text-xs font-bold py-2 px-4 rounded-xl w-full hover:scale-105 transition-transform">
                        Ver Detalles
                    </button>
                </div>

                {/* Decoracion */}
                <div className="absolute -right-4 -bottom-4 w-24 h-24 bg-white/20 rounded-full blur-xl group-hover:scale-150 transition-transform duration-500" />
            </div>
        </aside>
    );
}
