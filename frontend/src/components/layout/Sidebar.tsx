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
    Brain,
    Database,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { motion } from "framer-motion";

const menuItems = [
    { icon: LayoutDashboard, label: "Dashboard", href: "/" },
    { icon: Zap, label: "Predicciones", href: "/predictions" },
    { icon: BarChart2, label: "Estadísticas", href: "/stats" },
    { icon: Database, label: "Datos", href: "/database" },
    { icon: Brain, label: "Entrenamiento", href: "/training" },
    { icon: RefreshCcw, label: "Sincronización", href: "/sync" },
    { icon: Settings, label: "Configuración", href: "/settings" },
];

export function Sidebar() {
    const pathname = usePathname();

    return (
        <aside className="fixed left-6 top-6 bottom-6 w-64 rounded-[2rem] flex flex-col p-6 z-50 glass shadow-2xl overflow-hidden before:absolute before:inset-0 before:bg-gradient-to-b before:from-white/5 before:to-transparent before:pointer-events-none">
            {/* Logo */}
            <div className="flex items-center gap-3 px-2 mb-10 relative z-10">
                <div className="p-2.5 bg-sidebar-accent rounded-xl shadow-glow">
                    <Trophy className="w-5 h-5 text-sidebar-accent-foreground fill-current" />
                </div>
                <span className="text-xl font-bold text-sidebar-foreground tracking-tight">
                    Analizador<span className="text-sidebar-accent">Futbol</span>
                </span>
            </div>

            {/* Menu */}
            <nav className="flex-1 space-y-2 relative z-10">
                {menuItems.map((item) => {
                    const isActive = pathname === item.href;

                    return (
                        <Link
                            key={item.href}
                            href={item.href}
                            className="relative block group"
                        >
                            {isActive && (
                                <motion.div
                                    layoutId="activeTab"
                                    className="absolute inset-0 bg-sidebar-accent/10 rounded-xl border border-sidebar-accent/20 shadow-[0_0_20px_-5px_rgba(210,246,116,0.3)]"
                                    transition={{ type: "spring", stiffness: 300, damping: 30 }}
                                />
                            )}
                            <div
                                className={cn(
                                    "flex items-center gap-3 px-4 py-3.5 rounded-xl transition-all duration-200 relative z-10",
                                    isActive
                                        ? "text-sidebar-accent font-semibold"
                                        : "text-sidebar-muted hover:text-sidebar-foreground"
                                )}
                            >
                                <item.icon className={cn(
                                    "w-5 h-5 transition-transform duration-200 group-hover:scale-110",
                                    isActive ? "stroke-[2.5px]" : "stroke-2"
                                )} />
                                <span>{item.label}</span>
                                {isActive && (
                                    <div className="absolute right-3 w-1.5 h-1.5 rounded-full bg-sidebar-accent shadow-glow" />
                                )}
                            </div>
                        </Link>
                    );
                })}
            </nav>

            {/* Model Status Card */}
            <div className="relative z-10 mt-auto">
                <div className="bg-gradient-to-br from-[#1c1c20] to-[#121214] border border-white/5 rounded-2xl p-4 relative overflow-hidden group">
                    <div className="relative z-10">
                        <div className="flex items-center gap-2 mb-3">
                            <Activity className="w-4 h-4 text-sidebar-accent" />
                            <span className="text-xs font-bold text-sidebar-muted uppercase tracking-wider">Estado del Modelo</span>
                        </div>
                        <div className="flex items-end justify-between mb-4">
                            <div>
                                <span className="text-3xl font-bold text-white block">v1.2</span>
                                <span className="text-xs text-green-400 font-medium flex items-center gap-1 mt-1">
                                    <div className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" />
                                    Operativo
                                </span>
                            </div>
                            <div className="text-right">
                                <span className="text-2xl font-bold text-sidebar-accent">78.5%</span>
                                <span className="text-[10px] text-sidebar-muted block text-right">Precisión</span>
                            </div>
                        </div>
                        <button className="w-full py-2.5 bg-sidebar-accent/10 hover:bg-sidebar-accent/20 border border-sidebar-accent/20 text-sidebar-accent text-xs font-bold rounded-xl transition-all hover:shadow-glow flex items-center justify-center gap-2 group-hover:bg-sidebar-accent group-hover:text-sidebar-accent-foreground">
                            <Zap className="w-3.5 h-3.5" />
                            Ver Detalles
                        </button>
                    </div>
                </div>
            </div>

            {/* Background Glow */}
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full h-1/2 bg-sidebar-accent/5 blur-[100px] rounded-full pointer-events-none" />
        </aside>
    );
}
