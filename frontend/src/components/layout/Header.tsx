"use client";

import { Bell, Search } from "lucide-react";

export function Header() {
    return (
        <header className="flex items-center justify-between mb-8">
            <div>
                <h1 className="text-3xl font-bold text-foreground">
                    Hola, <span className="text-sidebar-muted">Jaime</span> 👋
                </h1>
                <p className="text-sidebar-muted font-medium mt-1">
                    Aquí están tus predicciones para hoy
                </p>
            </div>

            <div className="flex items-center gap-4">
                {/* Search */}
                <div className="hidden md:flex items-center gap-2 bg-white px-4 py-3 rounded-2xl shadow-sm w-80">
                    <Search className="w-5 h-5 text-sidebar-muted" />
                    <input
                        type="text"
                        placeholder="Buscar equipos, ligas..."
                        className="bg-transparent border-none outline-none text-sm font-medium w-full placeholder:text-gray-400"
                    />
                </div>

                {/* Notifications */}
                <button className="p-3 bg-white rounded-2xl shadow-sm relative hover:bg-gray-50 transition-colors">
                    <Bell className="w-6 h-6 text-foreground" />
                    <span className="absolute top-3 right-3 w-2 h-2 bg-red-500 rounded-full border-2 border-white"></span>
                </button>

                {/* Profile */}
                <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-sidebar-accent to-green-400 p-[2px]">
                    <div className="w-full h-full rounded-2xl bg-white overflow-hidden">
                        {/* Placeholder avatar */}
                        <div className="w-full h-full bg-sidebar flex items-center justify-center text-white font-bold">
                            JL
                        </div>
                    </div>
                </div>
            </div>
        </header>
    );
}
