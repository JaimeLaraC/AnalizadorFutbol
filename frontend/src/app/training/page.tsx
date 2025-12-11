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
    Terminal
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

export default function TrainingPage() {
    const [status, setStatus] = useState<TrainingStatus>({
        status: "idle",
        current_task: null,
        progress: 0,
        logs: [],
        error: null,
        result: null
    });

    const [seasons, setSeasons] = useState([2023, 2024]);

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

    const startCollect = async () => {
        try {
            await fetch("http://localhost:8000/training/collect", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ seasons })
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
                body: JSON.stringify({ min_matches: 5 })
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
                body: JSON.stringify({ test_size: 0.2, calibrate: true })
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
            color: "blue"
        },
        {
            id: 2,
            title: "Generar Features",
            description: "Calcula 69 features estadísticas por partido",
            icon: Cog,
            action: startFeatures,
            color: "purple"
        },
        {
            id: 3,
            title: "Entrenar Modelo",
            description: "XGBoost + LightGBM con calibración",
            icon: Brain,
            action: startTrain,
            color: "green"
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
                    Gestiona el pipeline de Machine Learning: recopilación, features y entrenamiento.
                </p>
            </div>

            {/* Steps Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                {steps.map((step, i) => (
                    <motion.div
                        key={step.id}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: i * 0.1 }}
                        className="bg-white rounded-3xl p-6 shadow-sm"
                    >
                        <div className={cn(
                            "w-14 h-14 rounded-2xl flex items-center justify-center mb-4",
                            step.color === "blue" && "bg-blue-100 text-blue-600",
                            step.color === "purple" && "bg-purple-100 text-purple-600",
                            step.color === "green" && "bg-green-100 text-green-600"
                        )}>
                            <step.icon className="w-7 h-7" />
                        </div>

                        <h3 className="text-lg font-bold text-foreground mb-1">
                            {step.id}. {step.title}
                        </h3>
                        <p className="text-sm text-sidebar-muted mb-4">
                            {step.description}
                        </p>

                        <button
                            onClick={step.action}
                            disabled={isRunning}
                            className={cn(
                                "w-full py-3 px-4 rounded-xl font-bold text-sm transition-all flex items-center justify-center gap-2",
                                isRunning
                                    ? "bg-gray-100 text-gray-400 cursor-not-allowed"
                                    : "bg-sidebar text-white hover:bg-sidebar/90"
                            )}
                        >
                            {isRunning && status.current_task?.includes(step.title.split(" ")[0]) ? (
                                <>
                                    <Loader2 className="w-4 h-4 animate-spin" />
                                    Procesando...
                                </>
                            ) : (
                                <>
                                    <Play className="w-4 h-4" />
                                    Ejecutar
                                </>
                            )}
                        </button>
                    </motion.div>
                ))}
            </div>

            {/* Status Card */}
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
                className="bg-white rounded-3xl p-6 shadow-sm mb-8"
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
                        <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                            <motion.div
                                className="h-full bg-sidebar-accent"
                                initial={{ width: 0 }}
                                animate={{ width: `${status.progress}%` }}
                                transition={{ duration: 0.5 }}
                            />
                        </div>
                        <p className="text-xs text-sidebar-muted mt-1 text-right">
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
                    <div className="flex items-center gap-2 p-3 bg-green-50 rounded-xl text-green-600 text-sm">
                        <CheckCircle2 className="w-4 h-4" />
                        Proceso completado exitosamente
                        {status.result.accuracy && (
                            <span className="ml-2 font-bold">
                                Precisión: {(status.result.accuracy * 100).toFixed(1)}%
                            </span>
                        )}
                    </div>
                )}
            </motion.div>

            {/* Logs Terminal */}
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.4 }}
                className="bg-sidebar rounded-3xl p-6 shadow-lg"
            >
                <div className="flex items-center gap-2 mb-4">
                    <Terminal className="w-5 h-5 text-sidebar-accent" />
                    <h3 className="text-lg font-bold text-white">Logs</h3>
                </div>

                <div className="bg-black/30 rounded-2xl p-4 h-64 overflow-y-auto font-mono text-sm">
                    {status.logs.length === 0 ? (
                        <p className="text-gray-500">Esperando acciones...</p>
                    ) : (
                        status.logs.map((log, i) => (
                            <p key={i} className="text-gray-300 leading-relaxed">
                                {log}
                            </p>
                        ))
                    )}
                </div>
            </motion.div>
        </div>
    );
}
