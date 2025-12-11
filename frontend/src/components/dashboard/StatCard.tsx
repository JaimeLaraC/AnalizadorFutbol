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
            className="bg-white p-6 rounded-3xl shadow-sm hover:shadow-md transition-shadow relative overflow-hidden group"
        >
            <div className="flex justify-between items-start mb-4">
                <div className="p-3 bg-sidebar/5 rounded-2xl group-hover:bg-sidebar-accent group-hover:text-sidebar transition-colors">
                    <Icon className="w-6 h-6 text-sidebar" />
                </div>
                {trend && (
                    <span className={cn(
                        "text-xs font-bold px-2 py-1 rounded-full",
                        trend.isPositive ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"
                    )}>
                        {trend.isPositive ? "+" : ""}{trend.value}%
                    </span>
                )}
            </div>

            <div>
                <h3 className="text-3xl font-bold text-foreground tracking-tighter mb-1">
                    {value}
                </h3>
                <p className="text-sm text-sidebar-muted font-medium mb-1">{label}</p>

                {subtext && (
                    <p className="text-xs text-sidebar-muted/80">{subtext}</p>
                )}
            </div>
        </motion.div>
    );
}
