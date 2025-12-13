"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
    Download,
    Cog,
    Brain,
    CheckCircle2,
    Play,
    Loader2,
    AlertCircle,
    Terminal,
    ChevronDown,
    ChevronUp,
    Settings2
} from "lucide-react";
import { cn } from "@/lib/utils";

interface TrainingStatus {
    status: "idle" | "running" | "completed" | "failed";
    current_task: string | null;
    progress: number;
    logs: string[];
    error: string | null;
    result: any | null;
}

// Ligas disponibles
const AVAILABLE_LEAGUES = [
    { id: 140, name: "La Liga", country: "España", flag: "🇪🇸" },
    { id: 39, name: "Premier League", country: "Inglaterra", flag: "🏴󠁧󠁢󠁥󠁮󠁧󠁿" },
    { id: 135, name: "Serie A", country: "Italia", flag: "🇮🇹" },
    { id: 78, name: "Bundesliga", country: "Alemania", flag: "🇩🇪" },
    { id: 61, name: "Ligue 1", country: "Francia", flag: "🇫🇷" },
    { id: 94, name: "Primeira Liga", country: "Portugal", flag: "🇵🇹" },
    { id: 88, name: "Eredivisie", country: "Países Bajos", flag: "🇳🇱" },
    { id: 144, name: "Jupiler Pro", country: "Bélgica", flag: "🇧🇪" },
];

const AVAILABLE_SEASONS = [2020, 2021, 2022, 2023, 2024];

export default function TrainingPage() {
    const [status, setStatus] = useState<TrainingStatus>({
        status: "idle",
        current_task: null,
        progress: 0,
        logs: [],
        error: null,
        result: null
    });

    // Estados de opciones expandidas
    const [expandedStep, setExpandedStep] = useState<number | null>(null);

    // Opciones de Recopilación
    const [selectedLeagues, setSelectedLeagues] = useState<number[]>([140, 39, 135]);
    const [selectedSeasons, setSelectedSeasons] = useState<number[]>([2023, 2024]);

    // Opciones de Features
    const [minMatches, setMinMatches] = useState(5);
    const [includeH2H, setIncludeH2H] = useState(true);
    const [includeForm, setIncludeForm] = useState(true);
    const [includeStandings, setIncludeStandings] = useState(true);

    // Opciones de Entrenamiento
    const [testSize, setTestSize] = useState(0.2);
    const [useCalibration, setUseCalibration] = useState(true);
    const [useXGBoost, setUseXGBoost] = useState(true);
    const [useLightGBM, setUseLightGBM] = useState(true);

    // Polling del estado
    useEffect(() => {
        const interval = setInterval(async () => {
            try {
                const res = await fetch("http://localhost:8000/training/status");
                const data = await res.json();
                setStatus(data);
            } catch (e) {
                console.error("Error fetching status:", e);
            }
        }, 1000);

        return () => clearInterval(interval);
    }, []);

    const toggleLeague = (id: number) => {
        setSelectedLeagues(prev =>
            prev.includes(id) ? prev.filter(l => l !== id) : [...prev, id]
        );
    };

    const toggleSeason = (year: number) => {
        setSelectedSeasons(prev =>
            prev.includes(year) ? prev.filter(y => y !== year) : [...prev, year]
        );
    };

    const startCollect = async () => {
        try {
            await fetch("http://localhost:8000/training/collect", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    seasons: selectedSeasons,
                    leagues: selectedLeagues
                })
            });
        } catch (e) {
            console.error("Error:", e);
        }
    };

    const startFeatures = async () => {
        try {
            await fetch("http://localhost:8000/training/features", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    min_matches: minMatches,
                    include_h2h: includeH2H,
                    include_form: includeForm,
                    include_standings: includeStandings
                })
            });
        } catch (e) {
            console.error("Error:", e);
        }
    };

    const startTrain = async () => {
        try {
            await fetch("http://localhost:8000/training/train", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    test_size: testSize,
                    calibrate: useCalibration,
                    use_xgboost: useXGBoost,
                    use_lightgbm: useLightGBM
                })
            });
        } catch (e) {
            console.error("Error:", e);
        }
    };

    const isRunning = status.status === "running";

    const steps = [
        {
            id: 1,
            title: "Recopilar Datos",
            description: "Descarga partidos históricos de API-Football",
            icon: Download,
            action: startCollect,
            color: "blue",
            summary: `${selectedLeagues.length} ligas, ${selectedSeasons.length} temporadas`
        },
        {
            id: 2,
            title: "Generar Features",
            description: "Calcula features estadísticas por partido",
            icon: Cog,
            action: startFeatures,
            color: "purple",
            summary: `Min ${minMatches} partidos${includeH2H ? ", H2H" : ""}${includeForm ? ", Forma" : ""}`
        },
        {
            id: 3,
            title: "Entrenar Modelo",
            description: "Entrena algoritmos de ML",
            icon: Brain,
            action: startTrain,
            color: "green",
            summary: `${useXGBoost ? "XGBoost" : ""}${useXGBoost && useLightGBM ? " + " : ""}${useLightGBM ? "LightGBM" : ""}, Test ${testSize * 100}%`
        }
    ];

    return (
        <div className="p-8 max-w-6xl mx-auto">
            {/* Header */}
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-foreground mb-2">
                    🏋️ Entrenamiento del Modelo
                </h1>
                <p className="text-sidebar-muted">
                    Configura y ejecuta el pipeline de Machine Learning paso a paso.
                </p>
            </div>

            {/* Steps */}
            <div className="space-y-4 mb-8">
                {steps.map((step, i) => (
                    <motion.div
                        key={step.id}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: i * 0.1 }}
                        className="glass rounded-3xl shadow-sm overflow-hidden"
                    >
                        {/* Step Header */}
                        <div
                            className="p-6 flex items-center gap-4 cursor-pointer hover:bg-card-foreground/5 transition-colors"
                            onClick={() => setExpandedStep(expandedStep === step.id ? null : step.id)}
                        >
                            <div className={cn(
                                "w-14 h-14 rounded-2xl flex items-center justify-center shrink-0",
                                step.color === "blue" && "bg-blue-100 text-blue-600",
                                step.color === "purple" && "bg-purple-100 text-purple-600",
                                step.color === "green" && "bg-green-100 text-green-600"
                            )}>
                                <step.icon className="w-7 h-7" />
                            </div>

                            <div className="flex-1">
                                <h3 className="text-lg font-bold text-foreground">
                                    {step.id}. {step.title}
                                </h3>
                                <p className="text-sm text-sidebar-muted">
                                    {step.description}
                                </p>
                                <p className="text-xs text-sidebar-accent font-medium mt-1">
                                    {step.summary}
                                </p>
                            </div>

                            <button
                                onClick={(e) => {
                                    e.stopPropagation();
                                    step.action();
                                }}
                                disabled={isRunning}
                                className={cn(
                                    "py-3 px-6 rounded-xl font-bold text-sm transition-all flex items-center gap-2 shrink-0",
                                    isRunning
                                        ? "bg-gray-100 text-gray-400 cursor-not-allowed"
                                        : "bg-sidebar text-white hover:bg-sidebar/90"
                                )}
                            >
                                {isRunning && status.current_task?.includes(step.title.split(" ")[0]) ? (
                                    <>
                                        <Loader2 className="w-4 h-4 animate-spin" />
                                        {status.progress}%
                                    </>
                                ) : (
                                    <>
                                        <Play className="w-4 h-4" />
                                        Ejecutar
                                    </>
                                )}
                            </button>

                            <button className="p-2 hover:bg-gray-100 rounded-full transition-colors">
                                {expandedStep === step.id ? (
                                    <ChevronUp className="w-5 h-5 text-gray-400" />
                                ) : (
                                    <ChevronDown className="w-5 h-5 text-gray-400" />
                                )}
                            </button>
                        </div>

                        {/* Expanded Options */}
                        {expandedStep === step.id && (
                            <motion.div
                                initial={{ height: 0, opacity: 0 }}
                                animate={{ height: "auto", opacity: 1 }}
                                exit={{ height: 0, opacity: 0 }}
                                className="border-t border-card-border p-6 bg-card-foreground/[0.02]"
                            >
                                {/* Step 1: Recopilación */}
                                {step.id === 1 && (
                                    <div className="space-y-6">
                                        <div>
                                            <h4 className="font-bold text-sm mb-3 flex items-center gap-2">
                                                <Settings2 className="w-4 h-4" />
                                                Ligas a recopilar
                                            </h4>
                                            <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                                                {AVAILABLE_LEAGUES.map(league => (
                                                    <button
                                                        key={league.id}
                                                        onClick={() => toggleLeague(league.id)}
                                                        className={cn(
                                                            "p-3 rounded-xl text-left transition-all border-2",
                                                            selectedLeagues.includes(league.id)
                                                                ? "border-sidebar-accent bg-sidebar-accent/10"
                                                                : "border-gray-200 hover:border-gray-300"
                                                        )}
                                                    >
                                                        <span className="text-lg">{league.flag}</span>
                                                        <p className="font-bold text-sm">{league.name}</p>
                                                        <p className="text-xs text-gray-500">{league.country}</p>
                                                    </button>
                                                ))}
                                            </div>
                                        </div>

                                        <div>
                                            <h4 className="font-bold text-sm mb-3">Temporadas</h4>
                                            <div className="flex gap-2">
                                                {AVAILABLE_SEASONS.map(year => (
                                                    <button
                                                        key={year}
                                                        onClick={() => toggleSeason(year)}
                                                        className={cn(
                                                            "px-4 py-2 rounded-xl font-bold text-sm transition-all border-2",
                                                            selectedSeasons.includes(year)
                                                                ? "border-sidebar-accent bg-sidebar-accent text-sidebar"
                                                                : "border-gray-200 hover:border-gray-300"
                                                        )}
                                                    >
                                                        {year}/{year + 1}
                                                    </button>
                                                ))}
                                            </div>
                                        </div>
                                    </div>
                                )}

                                {/* Step 2: Features */}
                                {step.id === 2 && (
                                    <div className="space-y-6">
                                        <div>
                                            <h4 className="font-bold text-sm mb-3">Mínimo de partidos por equipo</h4>
                                            <input
                                                type="range"
                                                min="1"
                                                max="20"
                                                value={minMatches}
                                                onChange={(e) => setMinMatches(parseInt(e.target.value))}
                                                className="w-full accent-sidebar-accent"
                                            />
                                            <p className="text-sm text-gray-500 mt-1">
                                                {minMatches} partidos mínimo
                                            </p>
                                        </div>

                                        <div>
                                            <h4 className="font-bold text-sm mb-3">Features a incluir</h4>
                                            <div className="space-y-2">
                                                {[
                                                    { label: "Head-to-Head (H2H)", value: includeH2H, setter: setIncludeH2H },
                                                    { label: "Forma reciente (últimos 5)", value: includeForm, setter: setIncludeForm },
                                                    { label: "Clasificación liga", value: includeStandings, setter: setIncludeStandings },
                                                ].map(feature => (
                                                    <label key={feature.label} className="flex items-center gap-3 cursor-pointer">
                                                        <input
                                                            type="checkbox"
                                                            checked={feature.value}
                                                            onChange={(e) => feature.setter(e.target.checked)}
                                                            className="w-5 h-5 rounded accent-sidebar-accent"
                                                        />
                                                        <span className="text-sm">{feature.label}</span>
                                                    </label>
                                                ))}
                                            </div>
                                        </div>
                                    </div>
                                )}

                                {/* Step 3: Entrenamiento */}
                                {step.id === 3 && (
                                    <div className="space-y-6">
                                        <div>
                                            <h4 className="font-bold text-sm mb-3">Proporción de test</h4>
                                            <input
                                                type="range"
                                                min="0.1"
                                                max="0.4"
                                                step="0.05"
                                                value={testSize}
                                                onChange={(e) => setTestSize(parseFloat(e.target.value))}
                                                className="w-full accent-sidebar-accent"
                                            />
                                            <p className="text-sm text-gray-500 mt-1">
                                                {(testSize * 100).toFixed(0)}% para validación
                                            </p>
                                        </div>

                                        <div>
                                            <h4 className="font-bold text-sm mb-3">Modelos a entrenar</h4>
                                            <div className="flex gap-4">
                                                {[
                                                    { label: "XGBoost", value: useXGBoost, setter: setUseXGBoost },
                                                    { label: "LightGBM", value: useLightGBM, setter: setUseLightGBM },
                                                ].map(model => (
                                                    <label key={model.label} className="flex items-center gap-3 cursor-pointer">
                                                        <input
                                                            type="checkbox"
                                                            checked={model.value}
                                                            onChange={(e) => model.setter(e.target.checked)}
                                                            className="w-5 h-5 rounded accent-sidebar-accent"
                                                        />
                                                        <span className="text-sm font-medium">{model.label}</span>
                                                    </label>
                                                ))}
                                            </div>
                                        </div>

                                        <div>
                                            <label className="flex items-center gap-3 cursor-pointer">
                                                <input
                                                    type="checkbox"
                                                    checked={useCalibration}
                                                    onChange={(e) => setUseCalibration(e.target.checked)}
                                                    className="w-5 h-5 rounded accent-sidebar-accent"
                                                />
                                                <div>
                                                    <span className="text-sm font-medium">Calibración de probabilidades</span>
                                                    <p className="text-xs text-gray-500">Platt Scaling para probabilidades más precisas</p>
                                                </div>
                                            </label>
                                        </div>
                                    </div>
                                )}
                            </motion.div>
                        )}
                    </motion.div>
                ))}
            </div>

            {/* Status Card */}
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
                className="glass rounded-3xl p-6 shadow-sm mb-8"
            >
                <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-bold text-foreground">Estado Actual</h3>
                    <div className={cn(
                        "px-3 py-1 rounded-full text-sm font-bold",
                        status.status === "idle" && "bg-gray-100 text-gray-600",
                        status.status === "running" && "bg-blue-100 text-blue-600",
                        status.status === "completed" && "bg-green-100 text-green-600",
                        status.status === "failed" && "bg-red-100 text-red-600"
                    )}>
                        {status.status === "idle" && "Inactivo"}
                        {status.status === "running" && "En Proceso"}
                        {status.status === "completed" && "Completado"}
                        {status.status === "failed" && "Error"}
                    </div>
                </div>

                {status.current_task && (
                    <div className="mb-4">
                        <p className="text-sm text-sidebar-muted mb-2">
                            {status.current_task}
                        </p>
                        <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
                            <motion.div
                                className="h-full bg-gradient-to-r from-sidebar-accent to-green-400"
                                initial={{ width: 0 }}
                                animate={{ width: `${status.progress}%` }}
                                transition={{ duration: 0.5 }}
                            />
                        </div>
                        <p className="text-xs text-sidebar-muted mt-1 text-right font-bold">
                            {status.progress}%
                        </p>
                    </div>
                )}

                {status.error && (
                    <div className="flex items-center gap-2 p-3 bg-red-50 rounded-xl text-red-600 text-sm">
                        <AlertCircle className="w-4 h-4" />
                        {status.error}
                    </div>
                )}

                {status.result && status.status === "completed" && (
                    <div className="p-4 bg-green-50 rounded-xl">
                        <div className="flex items-center gap-2 text-green-600 mb-2">
                            <CheckCircle2 className="w-5 h-5" />
                            <span className="font-bold">Proceso completado</span>
                        </div>
                        {status.result.accuracy && (
                            <div className="grid grid-cols-4 gap-4 mt-3">
                                <div className="text-center">
                                    <p className="text-2xl font-bold text-green-700">{(status.result.accuracy * 100).toFixed(1)}%</p>
                                    <p className="text-xs text-gray-500">Accuracy</p>
                                </div>
                                <div className="text-center">
                                    <p className="text-2xl font-bold text-green-700">{(status.result.precision * 100).toFixed(1)}%</p>
                                    <p className="text-xs text-gray-500">Precision</p>
                                </div>
                                <div className="text-center">
                                    <p className="text-2xl font-bold text-green-700">{(status.result.recall * 100).toFixed(1)}%</p>
                                    <p className="text-xs text-gray-500">Recall</p>
                                </div>
                                <div className="text-center">
                                    <p className="text-2xl font-bold text-green-700">{(status.result.f1_score * 100).toFixed(1)}%</p>
                                    <p className="text-xs text-gray-500">F1 Score</p>
                                </div>
                            </div>
                        )}
                        {status.result.total_fixtures && (
                            <p className="text-sm text-gray-600 mt-2">
                                ✅ {status.result.total_fixtures} partidos recopilados de {status.result.leagues} ligas
                            </p>
                        )}
                        {status.result.rows && (
                            <p className="text-sm text-gray-600 mt-2">
                                ✅ Dataset con {status.result.rows} filas y {status.result.columns} columnas
                            </p>
                        )}
                    </div>
                )}
            </motion.div>

            {/* Logs Terminal */}
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.4 }}
                className="bg-[#18181b] rounded-3xl p-6 shadow-lg border border-white/10"
            >
                <div className="flex items-center gap-2 mb-4">
                    <Terminal className="w-5 h-5 text-sidebar-accent" />
                    <h3 className="text-lg font-bold text-white">Logs</h3>
                    <span className="ml-auto text-xs text-gray-400 font-mono">
                        {status.logs.length} líneas
                    </span>
                </div>

                <div className="bg-black/30 rounded-2xl p-4 h-64 overflow-y-auto font-mono text-sm scroll-smooth">
                    {status.logs.length === 0 ? (
                        <p className="text-gray-500">Esperando acciones...</p>
                    ) : (
                        status.logs.map((log, i) => (
                            <p
                                key={i}
                                className={cn(
                                    "leading-relaxed",
                                    log.includes("✅") && "text-green-400",
                                    log.includes("❌") && "text-red-400",
                                    log.includes("⚠️") && "text-yellow-400",
                                    !log.includes("✅") && !log.includes("❌") && !log.includes("⚠️") && "text-gray-300"
                                )}
                            >
                                {log}
                            </p>
                        ))
                    )}
                </div>
            </motion.div>
        </div>
    );
}
