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
            className="bg-white p-4 rounded-3xl border border-gray-100 hover:border-sidebar-accent/50 transition-colors flex items-center justify-between group"
        >
            <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-2xl bg-gray-50 flex items-center justify-center text-lg font-bold text-gray-400">
                    VS
                </div>
                <div>
                    <h4 className="font-bold text-foreground text-sm mb-0.5">
                        {homeTeam} vs {awayTeam}
                    </h4>
                    <p className="text-xs text-sidebar-muted flex items-center gap-1">
                        <span className="w-1.5 h-1.5 rounded-full bg-sidebar-accent"></span>
                        {league} • {time}
                    </p>
                </div>
            </div>

            <div className="flex items-center gap-4">
                <div className="flex flex-col items-end">
                    <span className="text-xs font-medium text-sidebar-muted">Confianza</span>
                    <div className="flex items-center gap-1">
                        {/* Progress circle mini */}
                        <div className="w-8 h-8 rounded-full border-2 border-sidebar-accent flex items-center justify-center text-[10px] font-bold">
                            {probability}%
                        </div>
                    </div>
                </div>

                <button className="p-2 rounded-full hover:bg-gray-50 transition-colors">
                    <ChevronRight className="w-5 h-5 text-gray-400 group-hover:text-sidebar transition-colors" />
                </button>
            </div>
        </motion.div>
    );
}
