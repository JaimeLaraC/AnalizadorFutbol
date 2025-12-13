"use client";

import { useEffect, useState } from "react";
import { Header } from "@/components/layout/Header";
import { StatCard } from "@/components/dashboard/StatCard";
import { MatchCard } from "@/components/dashboard/MatchCard";
import { Activity, Target, Trophy, TrendingUp, Calendar, ChevronRight, Loader2 } from "lucide-react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { getPredictionsToday, getAccuracyStats, getDailyStats } from "@/lib/api";
import type { PredictionDetail, AccuracyStats, DailyStats } from "@/lib/types";

export default function Home() {
  const [predictions, setPredictions] = useState<PredictionDetail[]>([]);
  const [accuracyStats, setAccuracyStats] = useState<AccuracyStats | null>(null);
  const [dailyStats, setDailyStats] = useState<DailyStats[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentDate, setCurrentDate] = useState<Date | null>(null);

  useEffect(() => {
    async function fetchDashboardData() {
      try {
        setLoading(true);
        setError(null);

        const [predictionsRes, accuracyRes, dailyRes] = await Promise.all([
          getPredictionsToday(),
          getAccuracyStats(30),
          getDailyStats(7),
        ]);

        setPredictions(predictionsRes.predictions || []);
        setAccuracyStats(accuracyRes);
        setDailyStats(dailyRes);
      } catch (err) {
        console.error("Error fetching dashboard data:", err);
        setError("Error al cargar los datos. Verifica que el backend esté corriendo.");
      } finally {
        setLoading(false);
      }
    }

    fetchDashboardData();
    setCurrentDate(new Date());
  }, []);

  // Calcular valores para los StatCards
  const predictionsToday = predictions.length;
  // const completedPredictions = predictions.filter(p => p.actual_result !== null).length;
  const accuracyPercent = accuracyStats ? Math.round(accuracyStats.accuracy * 100) : 0;
  // const correctPredictions = accuracyStats?.correct || 0;
  // const totalPredictions = accuracyStats?.total_predictions || 0;
  const roiPercent = accuracyStats?.roi_percent || 0;

  // Calcular datos para el gráfico semanal
  const weeklyData = dailyStats.length > 0
    ? dailyStats.slice(0, 7).reverse().map(d => Math.round(d.accuracy * 100))
    : [0, 0, 0, 0, 0, 0, 0];

  const maxAccuracy = Math.max(...weeklyData, 1);
  const bestDayIndex = weeklyData.indexOf(Math.max(...weeklyData));

  // Formatear la hora del partido
  const formatMatchTime = (dateStr: string | null) => {
    if (!dateStr) return "--:--";
    const date = new Date(dateStr);
    return date.toLocaleTimeString("es-ES", { hour: "2-digit", minute: "2-digit" });
  };

  if (loading) {
    return (
      <div className="p-2">
        <Header />
        <div className="flex items-center justify-center h-96">
          <Loader2 className="w-8 h-8 animate-spin text-sidebar-accent" />
          <span className="ml-3 text-sidebar-muted">Cargando datos...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-2">
        <Header />
        <div className="flex flex-col items-center justify-center h-96">
          <p className="text-red-400 mb-4">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-sidebar text-white rounded-xl hover:bg-sidebar/90 border border-white/10"
          >
            Reintentar
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-2 pb-10">
      <Header />

      {/* Hero Section / Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <StatCard
          label="Predicciones Hoy"
          value={predictionsToday.toString()}
          subtext="Partidos analizados"
          icon={Activity}
          trend={{ value: 12, isPositive: true }}
          delay={0.1}
        />
        <StatCard
          label="Precisión Global"
          value={`${accuracyPercent}%`}
          subtext="Últimos 30 días"
          icon={Target}
          trend={{ value: 2.1, isPositive: true }}
          delay={0.2}
        />
        <StatCard
          label="ROI Mensual"
          value={`${roiPercent > 0 ? '+' : ''}${roiPercent}%`}
          subtext="Retorno de inversión"
          icon={TrendingUp}
          trend={{ value: 0.8, isPositive: roiPercent >= 0 }}
          delay={0.3}
        />
      </div>

      <div className="grid grid-cols-12 gap-8">
        {/* Main Content - Active Predictions */}
        <div className="col-span-12 lg:col-span-8 space-y-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-card-foreground flex items-center gap-2">
              <Trophy className="w-5 h-5 text-sidebar-accent" />
              Predicciones Activas
            </h2>
            <button className="text-sm font-medium text-sidebar-muted hover:text-card-foreground transition-colors flex items-center gap-1 group">
              Ver todo <ChevronRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </button>
          </div>

          <div className="space-y-4">
            {predictions.length > 0 ? (
              predictions.map((match, i) => (
                <MatchCard
                  key={match.fixture_id || i}
                  homeTeam={match.home_team_name || "Local"}
                  awayTeam={match.away_team_name || "Visitante"}
                  league={match.league_name || "Liga"}
                  time={match.match_date ? new Date(match.match_date).toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' }) : "--:--"}
                  probability={Math.round((match.predicted_winner === 1 ? match.probability_home : match.probability_away) * 100)}
                  prediction={(match.predicted_winner?.toString() as "1" | "2") || "1"}
                  delay={0.4 + (i * 0.1)}
                />
              ))
            ) : (
              <div className="glass rounded-[2rem] p-12 text-center border-dashed border-card-border">
                <div className="w-16 h-16 bg-sidebar-accent/10 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Target className="w-8 h-8 text-sidebar-accent" />
                </div>
                <h3 className="text-card-foreground font-bold mb-2">No hay predicciones activas</h3>
                <p className="text-sidebar-muted text-sm">El modelo no ha encontrado partidos para analizar hoy.</p>
              </div>
            )}
          </div>
        </div>

        {/* Sidebar Widgets */}
        <div className="col-span-12 lg:col-span-4 space-y-8">

          {/* Calendar Widget */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5, delay: 0.5 }}
            className="rounded-[2rem] glass p-6 relative overflow-hidden group"
          >
            <div className="absolute inset-0 bg-gradient-to-b from-card-foreground/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none" />

            <div className="flex items-center justify-between mb-6 relative z-10">
              <h3 className="font-bold text-card-foreground flex items-center gap-2">
                <Calendar className="w-5 h-5 text-sidebar-accent" />
                Calendario
              </h3>
              <span className="text-xs font-bold bg-card-foreground/10 text-card-foreground px-3 py-1 rounded-full border border-card-border">
                {currentDate?.toLocaleDateString('es-ES', { month: 'long', year: 'numeric' })}
              </span>
            </div>

            <div className="grid grid-cols-7 gap-1 text-center mb-2">
              {["L", "M", "M", "J", "V", "S", "D"].map((d, index) => (
                <span key={index} className="text-xs font-bold text-sidebar-muted py-2">{d}</span>
              ))}
            </div>

            <div className="grid grid-cols-7 gap-1 text-center relative z-10">
              {/* Días mockup para visualización - Idealmente dinámico */}
              {Array.from({ length: 30 }).map((_, i) => (
                <div
                  key={i}
                  className={cn(
                    "aspect-square flex items-center justify-center text-xs rounded-lg transition-all cursor-pointer",
                    i === 11 // Día actual (mock)
                      ? "bg-sidebar-accent text-sidebar-accent-foreground font-bold shadow-glow"
                      : "text-card-foreground/60 hover:bg-card-foreground/5 hover:text-card-foreground"
                  )}
                >
                  {i + 1}
                </div>
              ))}
            </div>
          </motion.div>

          {/* Performance Chart Widget */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5, delay: 0.6 }}
            className="rounded-[2rem] glass p-6 relative overflow-hidden"
          >
            <div className="flex items-center justify-between mb-6">
              <h3 className="font-bold text-card-foreground flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-sidebar-accent" />
                Rendimiento
              </h3>
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-sidebar-accent animate-pulse"></span>
                <span className="text-xs text-sidebar-muted">Esta semana</span>
              </div>
            </div>

            <div className="h-40 flex items-end justify-between gap-2 px-2">
              {weeklyData.map((val, i) => {
                const heightPercent = (val / maxAccuracy) * 100;
                return (
                  <div key={i} className="flex-1 flex flex-col items-center gap-2 group">
                    <div className="w-full relative h-32 flex items-end justify-center">
                      <motion.div
                        initial={{ height: 0 }}
                        animate={{ height: `${heightPercent}%` }}
                        transition={{ duration: 1, delay: 0.5 + (i * 0.1), type: "spring" }}
                        className={cn(
                          "w-full rounded-t-lg transition-all duration-300 relative min-h-[4px]",
                          i === bestDayIndex
                            ? "bg-sidebar-accent shadow-[0_0_15px_-5px_var(--sidebar-accent)]"
                            : "bg-card-foreground/10 group-hover:bg-card-foreground/20"
                        )}
                      >
                        <div className={cn(
                          "absolute -top-6 left-1/2 -translate-x-1/2 text-[10px] font-bold opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap",
                          i === bestDayIndex ? "text-sidebar-accent" : "text-card-foreground"
                        )}>
                          {val}%
                        </div>
                      </motion.div>
                    </div>
                    <span className="text-[10px] font-bold text-sidebar-muted text-center w-full">
                      {["L", "M", "M", "J", "V", "S", "D"][i]}
                    </span>
                  </div>
                );
              })}
            </div>
          </motion.div>

        </div>
      </div>
    </div>
  );
}
