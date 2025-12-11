"use client";

import { Header } from "@/components/layout/Header";
import { StatCard } from "@/components/dashboard/StatCard";
import { MatchCard } from "@/components/dashboard/MatchCard";
import { Activity, Target, Trophy, TrendingUp, Calendar, ChevronRight } from "lucide-react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

export default function Home() {
  return (
    <div className="p-2">
      <Header />

      {/* Main Grid */}
      <div className="grid grid-cols-12 gap-8">

        {/* Left Column (Stats + Chart) */}
        <div className="col-span-12 lg:col-span-8 space-y-8">

          {/* Stats Row */}
          <div>
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-bold text-foreground">Resumen de Hoy</h2>
              <button className="text-sm font-medium text-sidebar-muted hover:text-sidebar transition-colors">
                Ver todo
              </button>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <StatCard
                label="Predicciones Hoy"
                value="5"
                subtext="2 terminados"
                icon={Target}
                trend={{ value: 12, isPositive: true }}
                delay={0.1}
              />
              <StatCard
                label="Precisión Ayer"
                value="80%"
                subtext="4 de 5 acertadas"
                icon={Trophy}
                trend={{ value: 5, isPositive: true }}
                delay={0.2}
              />
              <StatCard
                label="ROI Mensual"
                value="+15.4%"
                subtext="Beneficio estimado"
                icon={TrendingUp}
                trend={{ value: 2.1, isPositive: true }}
                delay={0.3}
              />
            </div>
          </div>

          {/* Activity Chart Section (Mock placeholder for chart) */}
          <div className="bg-white p-8 rounded-3xl shadow-sm">
            <div className="flex items-center justify-between mb-8">
              <div>
                <h3 className="text-xl font-bold text-foreground">Rendimiento Semanal</h3>
                <div className="flex items-center gap-2 mt-1">
                  <span className="text-xs font-bold text-green-600 bg-green-100 px-2 py-0.5 rounded-full">
                    +3%
                  </span>
                  <span className="text-sm text-sidebar-muted">vs semana pasada</span>
                </div>
              </div>

              <select className="bg-gray-50 border-none text-sm font-medium p-2 rounded-xl outline-none">
                <option>Semanal</option>
                <option>Mensual</option>
              </select>
            </div>

            {/* Chart Area */}
            <div className="h-64 flex items-end justify-between gap-4 px-4">
              {[65, 45, 78, 52, 85, 48, 60].map((h, i) => (
                <div key={i} className="flex-1 flex flex-col items-center gap-2 group">
                  <div className="relative w-full">
                    <motion.div
                      initial={{ height: 0 }}
                      animate={{ height: `${h}%` }}
                      transition={{ duration: 1, delay: i * 0.1 }}
                      className={cn(
                        "w-full rounded-xl transition-all duration-300",
                        i === 4 ? "bg-sidebar-accent" : "bg-sidebar group-hover:bg-sidebar/80"
                      )}
                    />
                    {i === 4 && (
                      <div className="absolute -top-12 left-1/2 -translate-x-1/2 bg-sidebar text-white text-xs py-1 px-3 rounded-lg whitespace-nowrap">
                        85% Acierto
                        <div className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-sidebar"></div>
                      </div>
                    )}
                  </div>
                  <span className="text-xs font-medium text-sidebar-muted">
                    {["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"][i]}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Active Predictions List */}
          <div>
            <h2 className="text-xl font-bold text-foreground mb-6">Predicciones Activas</h2>
            <div className="space-y-4">
              <MatchCard
                homeTeam="Real Madrid" awayTeam="Barcelona"
                league="La Liga" time="21:00"
                probability={78} prediction="1"
                delay={0.4}
              />
              <MatchCard
                homeTeam="Arsenal" awayTeam="Liverpool"
                league="Premier League" time="18:30"
                probability={65} prediction="1"
                delay={0.5}
              />
              <MatchCard
                homeTeam="Juventus" awayTeam="AC Milan"
                league="Serie A" time="20:45"
                probability={82} prediction="1"
                delay={0.6}
              />
            </div>
          </div>

        </div>

        {/* Right Column (Widgets) */}
        <div className="col-span-12 lg:col-span-4 space-y-8">

          {/* Promo Card (like "Go Premium" in reference) */}
          <div className="bg-sidebar rounded-3xl p-6 text-white relative overflow-hidden">
            <div className="relative z-10">
              <div className="w-12 h-12 bg-white/10 rounded-2xl flex items-center justify-center mb-4 text-2xl">
                🚀
              </div>
              <h3 className="text-2xl font-bold mb-2">Versión Pro</h3>
              <p className="text-sidebar-muted text-sm mb-6">
                Accede a modelos avanzados y estadísticas detalladas de todas las ligas.
              </p>
              <button className="bg-sidebar-accent text-sidebar font-bold py-3 px-6 rounded-xl w-full hover:bg-white transition-colors">
                Actualizar Plan
              </button>
            </div>
            {/* BG Circles */}
            <div className="absolute top-0 right-0 w-32 h-32 bg-sidebar-accent/10 rounded-full blur-2xl -translate-y-1/2 translate-x-1/2"></div>
            <div className="absolute bottom-0 left-0 w-24 h-24 bg-blue-500/10 rounded-full blur-2xl translate-y-1/2 -translate-x-1/2"></div>
          </div>

          {/* Schedule Widget */}
          <div className="bg-white p-6 rounded-3xl shadow-sm">
            <div className="flex items-center justify-between mb-6">
              <h3 className="font-bold text-foreground">Calendario</h3>
              <button className="p-2 hover:bg-gray-50 rounded-full">
                <ChevronRight className="w-5 h-5 text-gray-400" />
              </button>
            </div>

            {/* Calendar Mock */}
            <div className="bg-gray-50 rounded-2xl p-4 mb-6">
              <div className="flex justify-between items-center text-sm font-bold text-sidebar-muted mb-4">
                <span>August, 2024</span>
              </div>
              <div className="grid grid-cols-7 gap-2 text-center text-xs font-medium">
                {["S", "M", "T", "W", "T", "F", "S"].map(d => (
                  <span key={d} className="text-gray-400">{d}</span>
                ))}
                {Array.from({ length: 31 }, (_, i) => i + 1).slice(0, 14).map((d) => (
                  <span key={d} className={cn(
                    "aspect-square flex items-center justify-center rounded-full cursor-pointer hover:bg-white",
                    d === 12 ? "bg-sidebar-accent text-sidebar font-bold shadow-sm" : "text-gray-600"
                  )}>{d}</span>
                ))}
              </div>
            </div>

            {/* Upcoming Task */}
            <div>
              <h4 className="font-bold text-sm mb-4">Próximos Eventos</h4>
              <div className="flex items-center gap-4 p-3 hover:bg-gray-50 rounded-2xl transition-colors cursor-pointer">
                <div className="w-10 h-10 rounded-xl bg-orange-100 flex items-center justify-center text-orange-600">
                  <Calendar className="w-5 h-5" />
                </div>
                <div>
                  <p className="font-bold text-sm">Entrenamiento Modelo</p>
                  <p className="text-xs text-gray-400">Hoy, 23:00</p>
                </div>
                <span className="ml-auto text-xs bg-gray-100 px-2 py-1 rounded-full text-gray-500">Wait</span>
              </div>
            </div>
          </div>

        </div>

      </div>
    </div>
  );
}
