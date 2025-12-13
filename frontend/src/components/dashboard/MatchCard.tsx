"use client";

import { motion } from "framer-motion";
import { Calendar, ChevronRight } from "lucide-react";

interface MatchCardProps {
    homeTeam: string;
    awayTeam: string;
    league: string;
    time: string;
    probability: number;
    prediction: "1" | "2";
    delay?: number;
}

export function MatchCard({ homeTeam, awayTeam, league, time, probability, prediction, delay = 0 }: MatchCardProps) {
    return (
        <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5, delay }}
            className="group relative flex items-center justify-between p-4 rounded-3xl glass hover:bg-card-foreground/5 hover:border-sidebar-accent/20 transition-all duration-300"
        >
            <div className="flex items-center gap-5">
                {/* VS Badge */}
                <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-card-foreground/5 to-card-foreground/10 border border-card-border flex items-center justify-center relative overflow-hidden group-hover:border-sidebar-accent/30 transition-colors">
                    <span className="text-sm font-black text-card-foreground/50 group-hover:text-sidebar-accent transition-colors relative z-10 italic">VS</span>
                    <div className="absolute inset-0 bg-sidebar-accent/0 group-hover:bg-sidebar-accent/5 transition-colors" />
                </div>

                <div>
                    <h4 className="font-bold text-card-foreground text-base mb-1">
                        {homeTeam} <span className="text-sidebar-muted font-normal mx-1">vs</span> {awayTeam}
                    </h4>
                    <div className="flex items-center gap-3">
                        <span className="text-xs font-bold text-sidebar-accent bg-sidebar-accent/10 px-2 py-0.5 rounded-md border border-sidebar-accent/20">
                            {prediction === "1" ? "Local" : "Visitante"}
                        </span>
                        <p className="text-xs text-sidebar-muted flex items-center gap-1.5 font-medium">
                            <span className="w-1 h-1 rounded-full bg-card-foreground/30"></span>
                            {league}
                        </p>
                        <p className="text-xs text-sidebar-muted flex items-center gap-1.5 font-medium">
                            <span className="w-1 h-1 rounded-full bg-card-foreground/30"></span>
                            {time}
                        </p>
                    </div>
                </div>
            </div>

            <div className="flex items-center gap-6">
                <div className="flex flex-col items-end">
                    <span className="text-[10px] uppercase tracking-wider font-bold text-sidebar-muted mb-1">Confianza</span>
                    <div className="flex items-center gap-2">
                        <div className="h-1.5 w-16 bg-card-foreground/10 rounded-full overflow-hidden">
                            <div
                                className="h-full bg-sidebar-accent rounded-full shadow-[0_0_10px_-2px_var(--sidebar-accent)]"
                                style={{ width: `${probability}%` }}
                            />
                        </div>
                        <span className="text-xs font-bold text-card-foreground tabular-nums">{probability}%</span>
                    </div>
                </div>

                <button className="w-10 h-10 rounded-full border border-card-border flex items-center justify-center hover:bg-sidebar-accent hover:text-black hover:border-sidebar-accent transition-all duration-300 shadow-lg group-hover:shadow-glow/30">
                    <ChevronRight className="w-5 h-5 text-card-foreground group-hover:text-black" />
                </button>
            </div>
        </motion.div>
    );
}
