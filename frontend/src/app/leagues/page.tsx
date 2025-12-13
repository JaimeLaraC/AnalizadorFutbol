"use client";

import { useState, useEffect } from "react";
import { Header } from "@/components/layout/Header";
import { motion } from "framer-motion";
import { Globe, Check, Download, Loader2, Search, Filter } from "lucide-react";
import { cn } from "@/lib/utils";

interface League {
    id: number;
    name: string;
    country: string;
    flag?: string;
    type: string;
    is_enabled: boolean;
    fixtures_count: number;
}

interface LeagueListResponse {
    total: number;
    enabled: number;
    leagues: League[];
}

export default function LeaguesPage() {
    const [leagues, setLeagues] = useState<League[]>([]);
    const [recommended, setRecommended] = useState<League[]>([]);
    const [loading, setLoading] = useState(true);
    const [selectedLeagues, setSelectedLeagues] = useState<Set<number>>(new Set());
    const [search, setSearch] = useState("");
    const [filter, setFilter] = useState<"all" | "enabled" | "recommended">("recommended");
    const [downloading, setDownloading] = useState(false);

    useEffect(() => {
        fetchLeagues();
    }, []);

    const fetchLeagues = async () => {
        setLoading(true);
        try {
            // Obtener ligas recomendadas
            const recRes = await fetch("http://localhost:8000/leagues/recommended");
            const recData = await recRes.json();
            setRecommended(recData);

            // Obtener todas las ligas
            const allRes = await fetch("http://localhost:8000/leagues/available");
            const allData: LeagueListResponse = await allRes.json();
            setLeagues(allData.leagues);

            // Pre-seleccionar las habilitadas
            const enabledIds = new Set(allData.leagues.filter(l => l.is_enabled).map(l => l.id));
            setSelectedLeagues(enabledIds);
        } catch (error) {
            console.error("Error fetching leagues:", error);
        } finally {
            setLoading(false);
        }
    };

    const toggleLeague = (id: number) => {
        setSelectedLeagues(prev => {
            const newSet = new Set(prev);
            if (newSet.has(id)) {
                newSet.delete(id);
            } else {
                newSet.add(id);
            }
            return newSet;
        });
    };

    const selectAllRecommended = () => {
        const recIds = new Set(recommended.map(l => l.id));
        setSelectedLeagues(recIds);
    };

    const handleDownload = async () => {
        setDownloading(true);
        try {
            const leagueIds = Array.from(selectedLeagues);
            const response = await fetch("http://localhost:8000/training/collect", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    seasons: [2023, 2024],
                    leagues: leagueIds
                })
            });

            if (response.ok) {
                alert(`Iniciada descarga de ${leagueIds.length} ligas. Revisa el estado en la página de entrenamiento.`);
            } else {
                alert("Error al iniciar la descarga");
            }
        } catch (error) {
            console.error("Error:", error);
            alert("Error de conexión");
        } finally {
            setDownloading(false);
        }
    };

    const filteredLeagues = () => {
        let list: League[] = [];

        if (filter === "recommended") {
            list = recommended;
        } else if (filter === "enabled") {
            list = leagues.filter(l => l.is_enabled);
        } else {
            list = leagues;
        }

        if (search) {
            const searchLower = search.toLowerCase();
            list = list.filter(l =>
                l.name.toLowerCase().includes(searchLower) ||
                l.country.toLowerCase().includes(searchLower)
            );
        }

        return list;
    };

    const groupedByCountry = () => {
        const grouped: Record<string, League[]> = {};
        for (const league of filteredLeagues()) {
            if (!grouped[league.country]) {
                grouped[league.country] = [];
            }
            grouped[league.country].push(league);
        }
        return grouped;
    };

    return (
        <div className="p-2">
            <Header />

            <div className="max-w-6xl mx-auto">
                {/* Title Section */}
                <div className="mb-8">
                    <h1 className="text-3xl font-bold text-foreground mb-2">
                        Gestión de Ligas
                    </h1>
                    <p className="text-sidebar-muted">
                        Selecciona las ligas para incluir en el dataset de entrenamiento
                    </p>
                </div>

                {/* Stats Bar */}
                <div className="grid grid-cols-3 gap-4 mb-8">
                    <div className="bg-white p-4 rounded-2xl shadow-sm">
                        <div className="text-3xl font-bold text-sidebar">{leagues.length}</div>
                        <div className="text-sm text-sidebar-muted">Ligas disponibles</div>
                    </div>
                    <div className="bg-white p-4 rounded-2xl shadow-sm">
                        <div className="text-3xl font-bold text-green-600">{selectedLeagues.size}</div>
                        <div className="text-sm text-sidebar-muted">Seleccionadas</div>
                    </div>
                    <div className="bg-white p-4 rounded-2xl shadow-sm">
                        <div className="text-3xl font-bold text-blue-600">{recommended.length}</div>
                        <div className="text-sm text-sidebar-muted">Recomendadas</div>
                    </div>
                </div>

                {/* Actions Bar */}
                <div className="flex items-center gap-4 mb-6">
                    {/* Search */}
                    <div className="flex-1 relative">
                        <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                        <input
                            type="text"
                            placeholder="Buscar liga o país..."
                            value={search}
                            onChange={(e) => setSearch(e.target.value)}
                            className="w-full pl-12 pr-4 py-3 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-sidebar-accent"
                        />
                    </div>

                    {/* Filter */}
                    <select
                        value={filter}
                        onChange={(e) => setFilter(e.target.value as "all" | "enabled" | "recommended")}
                        className="px-4 py-3 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-sidebar-accent"
                    >
                        <option value="recommended">🌟 Recomendadas ({recommended.length})</option>
                        <option value="enabled">✅ Habilitadas ({leagues.filter(l => l.is_enabled).length})</option>
                        <option value="all">🌍 Todas ({leagues.length})</option>
                    </select>

                    {/* Quick Actions */}
                    <button
                        onClick={selectAllRecommended}
                        className="px-4 py-3 bg-blue-50 text-blue-600 rounded-xl hover:bg-blue-100 transition-colors font-medium"
                    >
                        Seleccionar Recomendadas
                    </button>

                    {/* Download Button */}
                    <button
                        onClick={handleDownload}
                        disabled={selectedLeagues.size === 0 || downloading}
                        className={cn(
                            "px-6 py-3 rounded-xl font-bold flex items-center gap-2 transition-all",
                            selectedLeagues.size > 0 && !downloading
                                ? "bg-sidebar text-white hover:bg-sidebar/90"
                                : "bg-gray-200 text-gray-400 cursor-not-allowed"
                        )}
                    >
                        {downloading ? (
                            <>
                                <Loader2 className="w-5 h-5 animate-spin" />
                                Descargando...
                            </>
                        ) : (
                            <>
                                <Download className="w-5 h-5" />
                                Descargar Datos ({selectedLeagues.size})
                            </>
                        )}
                    </button>
                </div>

                {/* Leagues Grid */}
                {loading ? (
                    <div className="flex items-center justify-center py-20">
                        <Loader2 className="w-8 h-8 animate-spin text-sidebar" />
                    </div>
                ) : (
                    <div className="space-y-6">
                        {Object.entries(groupedByCountry()).map(([country, countryLeagues]) => (
                            <motion.div
                                key={country}
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                className="bg-white rounded-2xl shadow-sm overflow-hidden"
                            >
                                {/* Country Header */}
                                <div className="bg-gray-50 px-6 py-3 border-b flex items-center gap-3">
                                    <span className="text-2xl">{countryLeagues[0]?.flag || "🌍"}</span>
                                    <h3 className="font-bold text-foreground">{country}</h3>
                                    <span className="text-sm text-sidebar-muted">
                                        ({countryLeagues.length} ligas)
                                    </span>
                                </div>

                                {/* Leagues */}
                                <div className="divide-y">
                                    {countryLeagues.map((league) => (
                                        <div
                                            key={league.id}
                                            onClick={() => toggleLeague(league.id)}
                                            className={cn(
                                                "px-6 py-4 flex items-center gap-4 cursor-pointer transition-all hover:bg-gray-50",
                                                selectedLeagues.has(league.id) && "bg-green-50 hover:bg-green-100"
                                            )}
                                        >
                                            {/* Checkbox */}
                                            <div
                                                className={cn(
                                                    "w-6 h-6 rounded-lg border-2 flex items-center justify-center transition-all",
                                                    selectedLeagues.has(league.id)
                                                        ? "bg-green-500 border-green-500 text-white"
                                                        : "border-gray-300"
                                                )}
                                            >
                                                {selectedLeagues.has(league.id) && <Check className="w-4 h-4" />}
                                            </div>

                                            {/* League Info */}
                                            <div className="flex-1">
                                                <div className="font-semibold text-foreground">{league.name}</div>
                                                <div className="text-sm text-sidebar-muted">
                                                    ID: {league.id}
                                                    {league.is_enabled && (
                                                        <span className="ml-2 text-green-600">• Ya en BD</span>
                                                    )}
                                                    {league.fixtures_count > 0 && (
                                                        <span className="ml-2">• {league.fixtures_count} partidos</span>
                                                    )}
                                                </div>
                                            </div>

                                            {/* Status Badge */}
                                            {league.is_enabled && (
                                                <span className="px-3 py-1 bg-green-100 text-green-700 text-xs font-bold rounded-full">
                                                    ACTIVA
                                                </span>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            </motion.div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}
