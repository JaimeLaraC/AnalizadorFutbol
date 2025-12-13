"use client";

import { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";
import { motion } from "framer-motion";

interface StatCardProps {
    label: string;
    value: string;
    subtext?: string;
    icon: LucideIcon;
    trend?: {
        value: number;
        isPositive: boolean;
    };
    delay?: number;
}

export function StatCard({ label, value, subtext, icon: Icon, trend, delay = 0 }: StatCardProps) {
    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay }}
            className="group relative overflow-hidden rounded-[2rem] glass p-6 transition-all hover:bg-card-foreground/5 hover:shadow-glow/20"
        >
            <div className="flex justify-between items-start mb-6">
                <div className="p-3.5 bg-sidebar-accent/10 rounded-2xl group-hover:bg-sidebar-accent group-hover:text-sidebar-accent-foreground transition-all duration-300 ring-1 ring-inset ring-sidebar-accent/20 group-hover:ring-sidebar-accent">
                    <Icon className="w-6 h-6 text-sidebar-accent group-hover:text-sidebar-accent-foreground transition-colors" />
                </div>
                {trend && (
                    <div className={cn(
                        "flex items-center gap-1 text-xs font-bold px-3 py-1.5 rounded-full border backdrop-blur-sm",
                        trend.isPositive
                            ? "bg-green-500/10 border-green-500/20 text-green-500"
                            : "bg-red-500/10 border-red-500/20 text-red-500"
                    )}>
                        {trend.isPositive ? "+" : ""}{trend.value}%
                    </div>
                )}
            </div>

            <div>
                <h3 className="text-4xl font-bold text-card-foreground tracking-tighter mb-2">
                    {value}
                </h3>
                <p className="text-sm text-sidebar-muted font-medium mb-1 uppercase tracking-wider text-[11px]">{label}</p>

                {subtext && (
                    <p className="text-xs text-card-foreground/40">{subtext}</p>
                )}
            </div>

            {/* Hover Glow Effect */}
            <div className="absolute -right-10 -bottom-10 w-32 h-32 bg-sidebar-accent/5 rounded-full blur-[50px] group-hover:bg-sidebar-accent/10 transition-colors duration-500 pointer-events-none" />
        </motion.div>
    );
}
