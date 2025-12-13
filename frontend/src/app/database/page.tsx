"use client";

import { useState, useEffect } from "react";
import { Header } from "@/components/layout/Header";
import { motion } from "framer-motion";
import { Database, RefreshCw, Loader2, ChevronDown, ChevronUp } from "lucide-react";
import { cn } from "@/lib/utils";

interface LeagueStats {
    id: number;
    name: string;
    country: string;
    fixtures_count: number;
    seasons: number[];
}

interface DatabaseStats {
    total_fixtures: number;
    total_teams: number;
    total_leagues: number;
    leagues: LeagueStats[];
}

export default function DatabasePage() {
    const [stats, setStats] = useState<DatabaseStats | null>(null);
    const [loading, setLoading] = useState(true);
    const [expandedLeagues, setExpandedLeagues] = useState<Set<number>>(new Set());

    useEffect(() => {
        fetchStats();
    }, []);

    const fetchStats = async () => {
        setLoading(true);
        try {
            const response = await fetch("http://localhost:8000/stats/database");
            if (response.ok) {
                const data = await response.json();
                setStats(data);
            } else {
                // Fallback: obtener datos de ligas habilitadas
                const leaguesRes = await fetch("http://localhost:8000/leagues/enabled");
                if (leaguesRes.ok) {
                    const leagues = await leaguesRes.json();
                    setStats({
                        total_fixtures: leagues.reduce((sum: number, l: LeagueStats) => sum + (l.fixtures_count || 0), 0),
                        total_teams: 0,
                        total_leagues: leagues.length,
                        leagues: leagues.map((l: any) => ({
                            id: l.id,
                            name: l.name,
                            country: l.country,
                            fixtures_count: l.fixtures_count || 0,
                            seasons: []
                        }))
                    });
                }
            }
        } catch (error) {
            console.error("Error fetching stats:", error);
        } finally {
            setLoading(false);
        }
    };

    const toggleLeague = (id: number) => {
        setExpandedLeagues(prev => {
            const newSet = new Set(prev);
            if (newSet.has(id)) {
                newSet.delete(id);
            } else {
                newSet.add(id);
            }
            return newSet;
        });
    };

    return (
        <div className="p-2">
            <Header />

            <div className="max-w-6xl mx-auto">
                {/* Title Section */}
                <div className="flex items-center justify-between mb-8">
                    <div>
                        <h1 className="text-3xl font-bold text-foreground mb-2">
                            Base de Datos
                        </h1>
                        <p className="text-sidebar-muted">
                            Estado actual de los datos almacenados
                        </p>
                    </div>
                    <button
                        onClick={fetchStats}
                        disabled={loading}
                        className="flex items-center gap-2 px-4 py-2 bg-sidebar text-white rounded-xl hover:bg-sidebar/90 disabled:opacity-50"
                    >
                        <RefreshCw className={cn("w-4 h-4", loading && "animate-spin")} />
                        Actualizar
                    </button>
                </div>

                {loading ? (
                    <div className="flex items-center justify-center py-20">
                        <Loader2 className="w-8 h-8 animate-spin text-sidebar" />
                    </div>
                ) : stats ? (
                    <>
                        {/* Stats Cards */}
                        <div className="grid grid-cols-3 gap-6 mb-8">
                            <motion.div
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: 0.1 }}
                                className="bg-white p-6 rounded-2xl shadow-sm"
                            >
                                <div className="flex items-center gap-4">
                                    <div className="w-14 h-14 bg-blue-100 rounded-2xl flex items-center justify-center">
                                        <Database className="w-7 h-7 text-blue-600" />
                                    </div>
                                    <div>
                                        <div className="text-3xl font-bold text-foreground">
                                            {stats.total_fixtures.toLocaleString()}
                                        </div>
                                        <div className="text-sm text-sidebar-muted">Partidos Total</div>
                                    </div>
                                </div>
                            </motion.div>

                            <motion.div
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: 0.2 }}
                                className="bg-white p-6 rounded-2xl shadow-sm"
                            >
                                <div className="flex items-center gap-4">
                                    <div className="w-14 h-14 bg-green-100 rounded-2xl flex items-center justify-center">
                                        <span className="text-2xl">🏆</span>
                                    </div>
                                    <div>
                                        <div className="text-3xl font-bold text-foreground">
                                            {stats.total_leagues}
                                        </div>
                                        <div className="text-sm text-sidebar-muted">Ligas</div>
                                    </div>
                                </div>
                            </motion.div>

                            <motion.div
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: 0.3 }}
                                className="bg-white p-6 rounded-2xl shadow-sm"
                            >
                                <div className="flex items-center gap-4">
                                    <div className="w-14 h-14 bg-purple-100 rounded-2xl flex items-center justify-center">
                                        <span className="text-2xl">⚽</span>
                                    </div>
                                    <div>
                                        <div className="text-3xl font-bold text-foreground">
                                            {stats.total_teams || "-"}
                                        </div>
                                        <div className="text-sm text-sidebar-muted">Equipos</div>
                                    </div>
                                </div>
                            </motion.div>
                        </div>

                        {/* Leagues List */}
                        <div className="bg-white rounded-2xl shadow-sm overflow-hidden">
                            <div className="px-6 py-4 border-b bg-gray-50">
                                <h2 className="font-bold text-foreground">Ligas con Datos</h2>
                            </div>
                            <div className="divide-y">
                                {stats.leagues
                                    .filter(l => l.fixtures_count > 0)
                                    .sort((a, b) => b.fixtures_count - a.fixtures_count)
                                    .map((league) => (
                                        <div key={league.id} className="px-6 py-4">
                                            <div
                                                className="flex items-center justify-between cursor-pointer"
                                                onClick={() => toggleLeague(league.id)}
                                            >
                                                <div className="flex items-center gap-4">
                                                    <div className="text-2xl">
                                                        {getCountryFlag(league.country)}
                                                    </div>
                                                    <div>
                                                        <div className="font-semibold text-foreground">
                                                            {league.name}
                                                        </div>
                                                        <div className="text-sm text-sidebar-muted">
                                                            {league.country} • ID: {league.id}
                                                        </div>
                                                    </div>
                                                </div>
                                                <div className="flex items-center gap-4">
                                                    <div className="text-right">
                                                        <div className="font-bold text-foreground">
                                                            {league.fixtures_count.toLocaleString()}
                                                        </div>
                                                        <div className="text-xs text-sidebar-muted">partidos</div>
                                                    </div>
                                                    {expandedLeagues.has(league.id) ? (
                                                        <ChevronUp className="w-5 h-5 text-gray-400" />
                                                    ) : (
                                                        <ChevronDown className="w-5 h-5 text-gray-400" />
                                                    )}
                                                </div>
                                            </div>

                                            {expandedLeagues.has(league.id) && (
                                                <motion.div
                                                    initial={{ height: 0, opacity: 0 }}
                                                    animate={{ height: "auto", opacity: 1 }}
                                                    className="mt-4 pl-12"
                                                >
                                                    <div className="bg-gray-50 rounded-xl p-4">
                                                        <p className="text-sm text-sidebar-muted">
                                                            Temporadas disponibles: 2020/21 - 2024/25
                                                        </p>
                                                        <div className="mt-2 flex gap-2">
                                                            {[2020, 2021, 2022, 2023, 2024].map(year => (
                                                                <span
                                                                    key={year}
                                                                    className="px-3 py-1 bg-white rounded-lg text-sm font-medium border"
                                                                >
                                                                    {year}/{(year + 1).toString().slice(-2)}
                                                                </span>
                                                            ))}
                                                        </div>
                                                    </div>
                                                </motion.div>
                                            )}
                                        </div>
                                    ))}
                            </div>
                        </div>

                        {/* Empty Leagues */}
                        {stats.leagues.filter(l => l.fixtures_count === 0).length > 0 && (
                            <div className="mt-8 bg-white rounded-2xl shadow-sm overflow-hidden">
                                <div className="px-6 py-4 border-b bg-gray-50">
                                    <h2 className="font-bold text-foreground">Ligas sin Datos</h2>
                                    <p className="text-sm text-sidebar-muted">
                                        Estas ligas están en la BD pero sin partidos descargados
                                    </p>
                                </div>
                                <div className="p-6">
                                    <div className="flex flex-wrap gap-2">
                                        {stats.leagues
                                            .filter(l => l.fixtures_count === 0)
                                            .map((league) => (
                                                <span
                                                    key={league.id}
                                                    className="px-3 py-1 bg-gray-100 text-gray-600 rounded-full text-sm"
                                                >
                                                    {league.name}
                                                </span>
                                            ))}
                                    </div>
                                </div>
                            </div>
                        )}
                    </>
                ) : (
                    <div className="text-center py-20 text-sidebar-muted">
                        No se pudieron cargar los datos
                    </div>
                )}
            </div>
        </div>
    );
}

function getCountryFlag(country: string): string {
    const flags: Record<string, string> = {
        "England": "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
        "Spain": "🇪🇸",
        "Italy": "🇮🇹",
        "Germany": "🇩🇪",
        "France": "🇫🇷",
        "Netherlands": "🇳🇱",
        "Portugal": "🇵🇹",
        "Belgium": "🇧🇪",
        "Turkey": "🇹🇷",
        "Scotland": "🏴󠁧󠁢󠁳󠁣󠁴󠁿",
        "Argentina": "🇦🇷",
        "Brazil": "🇧🇷",
        "USA": "🇺🇸",
        "Mexico": "🇲🇽",
        "Japan": "🇯🇵",
        "South-Korea": "🇰🇷",
        "Australia": "🇦🇺",
    };
    return flags[country] || "🌍";
}
