"use client";

import { useEffect, useState } from "react";
import { Header } from "@/components/layout/Header";
import {
    Database,
    Table,
    ChevronRight,
    Loader2,
    RefreshCw,
    Search,
    ChevronLeft,
    Trash2,
    Edit2,
    X,
    Check,
    AlertTriangle,
    Zap,
    Settings2,
    ChevronDown
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import axios from "axios";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface TableInfo {
    name: string;
    columns: string[];
    row_count: number;
}

interface TableData {
    table_name: string;
    columns: string[];
    rows: Record<string, unknown>[];
    total: number;
    limit: number;
    offset: number;
}

interface ColumnInfo {
    name: string;
    type: string;
    nullable: boolean;
    primary_key: boolean;
}

interface TableSchema {
    name: string;
    columns: ColumnInfo[];
    row_count: number;
    primary_keys: string[];
}

export default function DatabasePage() {
    const [tables, setTables] = useState<TableInfo[]>([]);
    const [selectedTable, setSelectedTable] = useState<string | null>(null);
    const [tableData, setTableData] = useState<TableData | null>(null);
    const [tableSchema, setTableSchema] = useState<TableSchema | null>(null);
    const [loading, setLoading] = useState(true);
    const [loadingData, setLoadingData] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [page, setPage] = useState(0);
    const [searchTerm, setSearchTerm] = useState("");
    const [proMode, setProMode] = useState(false);
    const [editingRow, setEditingRow] = useState<number | null>(null);
    const [editData, setEditData] = useState<Record<string, unknown>>({});
    const [showDeleteConfirm, setShowDeleteConfirm] = useState<{ type: 'row' | 'table' | 'all', id?: number } | null>(null);
    const [notification, setNotification] = useState<{ type: 'success' | 'error', message: string } | null>(null);

    const ROWS_PER_PAGE = 20;

    useEffect(() => {
        fetchTables();
    }, []);

    useEffect(() => {
        if (notification) {
            const timer = setTimeout(() => setNotification(null), 3000);
            return () => clearTimeout(timer);
        }
    }, [notification]);

    async function fetchTables() {
        try {
            setLoading(true);
            const response = await axios.get<TableInfo[]>(`${API_URL}/database/tables`);
            setTables(response.data);
            setError(null);
        } catch (err) {
            console.error("Error fetching tables:", err);
            setError("Error al cargar las tablas");
        } finally {
            setLoading(false);
        }
    }

    async function fetchTableData(tableName: string, offset = 0) {
        try {
            setLoadingData(true);
            const [dataRes, schemaRes] = await Promise.all([
                axios.get<TableData>(`${API_URL}/database/tables/${tableName}`, {
                    params: { limit: ROWS_PER_PAGE, offset }
                }),
                axios.get<TableSchema>(`${API_URL}/database/schema/${tableName}`)
            ]);
            setTableData(dataRes.data);
            setTableSchema(schemaRes.data);
            setSelectedTable(tableName);
            setPage(offset / ROWS_PER_PAGE);
            setEditingRow(null);
        } catch (err) {
            console.error("Error fetching table data:", err);
            setError("Error al cargar los datos de la tabla");
        } finally {
            setLoadingData(false);
        }
    }

    async function deleteRow(tableName: string, rowId: number) {
        try {
            await axios.delete(`${API_URL}/database/tables/${tableName}/row/${rowId}`);
            setNotification({ type: 'success', message: `Registro ${rowId} eliminado` });
            fetchTableData(tableName, page * ROWS_PER_PAGE);
            fetchTables();
        } catch (err) {
            console.error("Error deleting row:", err);
            setNotification({ type: 'error', message: 'Error al eliminar el registro' });
        }
        setShowDeleteConfirm(null);
    }

    async function clearTable(tableName: string) {
        try {
            await axios.delete(`${API_URL}/database/tables/${tableName}/clear?confirm=true`);
            setNotification({ type: 'success', message: `Tabla ${tableName} vaciada` });
            fetchTableData(tableName);
            fetchTables();
        } catch (err) {
            console.error("Error clearing table:", err);
            setNotification({ type: 'error', message: 'Error al vaciar la tabla' });
        }
        setShowDeleteConfirm(null);
    }

    async function clearAllData() {
        try {
            const response = await axios.delete(`${API_URL}/database/clear-all?confirm=true`);
            setNotification({ type: 'success', message: response.data.message });
            setSelectedTable(null);
            setTableData(null);
            fetchTables();
        } catch (err) {
            console.error("Error clearing all data:", err);
            setNotification({ type: 'error', message: 'Error al limpiar la base de datos' });
        }
        setShowDeleteConfirm(null);
    }

    async function updateRow(tableName: string, rowId: number) {
        try {
            await axios.put(`${API_URL}/database/tables/${tableName}/row/${rowId}`, editData);
            setNotification({ type: 'success', message: `Registro ${rowId} actualizado` });
            setEditingRow(null);
            setEditData({});
            fetchTableData(tableName, page * ROWS_PER_PAGE);
        } catch (err) {
            console.error("Error updating row:", err);
            setNotification({ type: 'error', message: 'Error al actualizar el registro' });
        }
    }

    function startEditing(row: Record<string, unknown>) {
        setEditingRow(row.id as number);
        setEditData({ ...row });
    }

    const totalPages = tableData ? Math.ceil(tableData.total / ROWS_PER_PAGE) : 0;

    const filteredRows = tableData?.rows.filter(row => {
        if (!searchTerm) return true;
        return Object.values(row).some(
            val => val !== null && String(val).toLowerCase().includes(searchTerm.toLowerCase())
        );
    }) || [];

    const tableIcons: Record<string, string> = {
        predictions: "🎯",
        fixtures: "⚽",
        teams: "👥",
        leagues: "🏆",
        standings: "📋",
        team_statistics: "📊",
        head_to_head: "🔄",
        fixture_statistics: "📈"
    };

    const visibleColumns = proMode
        ? tableData?.columns || []
        : tableData?.columns.slice(0, 6) || [];

    if (loading) {
        return (
            <div className="p-2">
                <Header />
                <div className="flex items-center justify-center h-96">
                    <Loader2 className="w-8 h-8 animate-spin text-sidebar-accent" />
                    <span className="ml-3 text-sidebar-muted">Cargando tablas...</span>
                </div>
            </div>
        );
    }

    return (
        <div className="p-2">
            <Header />

            {/* Modo Pro Toggle */}
            <div className="mb-8 flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold text-card-foreground tracking-tight flex items-center gap-3">
                        Explorador de Base de Datos
                        <span className="px-3 py-1 bg-sidebar-accent/10 text-sidebar-accent text-xs rounded-full border border-sidebar-accent/20 font-bold tracking-wider uppercase">
                            Admin
                        </span>
                    </h1>
                    <p className="text-sidebar-muted mt-1 text-sm">Gestiona y visualiza directamente los registros del sistema</p>
                </div>

                <div className="flex items-center gap-4">
                    <button
                        onClick={() => setProMode(!proMode)}
                        className={cn(
                            "flex items-center gap-2 px-4 py-2.5 rounded-xl font-bold text-sm transition-all duration-300 border",
                            proMode
                                ? "bg-sidebar-accent text-sidebar-accent-foreground border-sidebar-accent shadow-glow"
                                : "bg-card-foreground/5 border-card-foreground/10 text-card-foreground hover:bg-card-foreground/10 hover:border-card-foreground/20"
                        )}
                    >
                        {proMode ? <Zap className="w-4 h-4 fill-current" /> : <Settings2 className="w-4 h-4" />}
                        {proMode ? "Modo Pro: ACTIVO" : "Modo Pro"}
                    </button>

                    {proMode && (
                        <button
                            onClick={() => setShowDeleteConfirm({ type: 'all' })}
                            className="flex items-center gap-2 px-4 py-2.5 rounded-xl font-bold text-sm bg-red-500/10 text-red-400 border border-red-500/20 hover:bg-red-500/20 hover:border-red-500/40 transition-all hover:shadow-[0_0_20px_-5px_rgba(239,68,68,0.3)]"
                        >
                            <Trash2 className="w-4 h-4" />
                            Limpiar Todo
                        </button>
                    )}
                </div>
            </div>

            <div className="grid grid-cols-12 gap-6">
                {/* Panel izquierdo - Lista de tablas */}
                <div className="col-span-12 lg:col-span-3">
                    <div className="glass rounded-[2rem] p-6 sticky top-6">
                        <div className="flex items-center justify-between mb-6">
                            <h2 className="text-sm font-bold text-sidebar-muted uppercase tracking-wider flex items-center gap-2">
                                <Database className="w-4 h-4" />
                                Tablas Disponibles
                            </h2>
                            <button
                                onClick={fetchTables}
                                className="p-2 hover:bg-white/10 rounded-lg transition-colors text-white/50 hover:text-white"
                            >
                                <RefreshCw className="w-3.5 h-3.5" />
                            </button>
                        </div>

                        <div className="space-y-2 max-h-[calc(100vh-300px)] overflow-y-auto pr-2 custom-scrollbar">
                            {tables.map((table) => (
                                <motion.button
                                    key={table.name}
                                    onClick={() => fetchTableData(table.name)}
                                    whileHover={{ x: 4 }}
                                    className={cn(
                                        "w-full flex items-center justify-between p-3 rounded-xl transition-all border",
                                        selectedTable === table.name
                                            ? "bg-sidebar-accent/10 border-sidebar-accent/20 shadow-glow/10"
                                            : "bg-transparent border-transparent hover:bg-card-foreground/5 hover:border-card-foreground/5"
                                    )}
                                >
                                    <div className="flex items-center gap-3">
                                        <span className="text-lg opacity-80">{tableIcons[table.name] || "📁"}</span>
                                        <div className="text-left">
                                            <p className={cn(
                                                "font-medium text-sm transition-colors",
                                                selectedTable === table.name ? "text-sidebar-accent" : "text-card-foreground/80"
                                            )}>{table.name}</p>
                                            <p className="text-[10px] text-gray-500">
                                                {table.row_count.toLocaleString()} filas
                                            </p>
                                        </div>
                                    </div>
                                    {selectedTable === table.name && (
                                        <motion.div layoutId="activeDot" className="w-1.5 h-1.5 rounded-full bg-sidebar-accent shadow-glow" />
                                    )}
                                </motion.button>
                            ))}
                        </div>

                        {/* Resumen */}
                        <div className="mt-6 pt-6 border-t border-white/5">
                            <div className="grid grid-cols-2 gap-3">
                                <div className="bg-white/5 rounded-xl p-3 border border-white/5">
                                    <p className="text-xl font-bold text-card-foreground mb-0.5">
                                        {tables.reduce((acc, t) => acc + t.row_count, 0).toLocaleString()}
                                    </p>
                                    <p className="text-[10px] font-medium text-sidebar-muted uppercase tracking-wider">Registros</p>
                                </div>
                                <div className="bg-white/5 rounded-xl p-3 border border-white/5">
                                    <p className="text-xl font-bold text-card-foreground mb-0.5">{tables.length}</p>
                                    <p className="text-[10px] font-medium text-sidebar-muted uppercase tracking-wider">Tablas</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Panel derecho - Datos de la tabla */}
                <div className="col-span-12 lg:col-span-9">
                    <AnimatePresence mode="wait">
                        {!selectedTable ? (
                            <motion.div
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                exit={{ opacity: 0 }}
                                className="glass rounded-[2rem] p-12 flex flex-col items-center justify-center min-h-[500px]"
                            >
                                <div className="w-20 h-20 bg-white/5 rounded-full flex items-center justify-center mb-6">
                                    <Table className="w-8 h-8 text-white/20" />
                                </div>
                                <h3 className="text-xl font-bold text-card-foreground mb-2">
                                    Selecciona una tabla
                                </h3>
                                <p className="text-sidebar-muted text-sm max-w-sm text-center">
                                    Explora los datos seleccionando una tabla del panel izquierdo. Podrás ver, editar y eliminar registros.
                                </p>
                            </motion.div>
                        ) : (
                            <motion.div
                                key={selectedTable}
                                initial={{ opacity: 0, scale: 0.98 }}
                                animate={{ opacity: 1, scale: 1 }}
                                exit={{ opacity: 0, scale: 0.98 }}
                                className="glass rounded-[2rem] overflow-hidden flex flex-col h-full min-h-[600px]"
                            >
                                {/* Header de la tabla */}
                                <div className="p-6 border-b border-white/5 bg-white/[0.02]">
                                    <div className="flex items-center justify-between flex-wrap gap-4">
                                        <div className="flex items-center gap-4">
                                            <div className="p-3 bg-sidebar-accent/10 rounded-xl border border-sidebar-accent/10">
                                                <span className="text-2xl">{tableIcons[selectedTable] || "📁"}</span>
                                            </div>
                                            <div>
                                                <h2 className="text-xl font-bold text-card-foreground flex items-center gap-2">
                                                    {selectedTable}
                                                    {proMode && (
                                                        <span className="px-2 py-0.5 rounded text-[10px] bg-white/10 text-white/60 border border-white/5">
                                                            {tableSchema?.columns.length} cols
                                                        </span>
                                                    )}
                                                </h2>
                                                <p className="text-sm text-sidebar-muted">
                                                    {tableData?.total.toLocaleString()} registros totales
                                                </p>
                                            </div>
                                        </div>

                                        <div className="flex items-center gap-3">
                                            {/* Búsqueda */}
                                            <div className="relative group">
                                                <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-card-foreground/30 group-focus-within:text-sidebar-accent transition-colors" />
                                                <input
                                                    type="text"
                                                    placeholder="Buscar registros..."
                                                    value={searchTerm}
                                                    onChange={(e) => setSearchTerm(e.target.value)}
                                                    className="pl-10 pr-4 py-2.5 bg-card-foreground/5 rounded-xl border border-card-border outline-none text-sm w-64 text-card-foreground focus:border-sidebar-accent/50 focus:ring-1 focus:ring-sidebar-accent/50 transition-all"
                                                />
                                            </div>

                                            {proMode && (
                                                <button
                                                    onClick={() => setShowDeleteConfirm({ type: 'table' })}
                                                    className="flex items-center gap-2 px-3 py-2.5 rounded-xl text-red-400 bg-red-500/10 border border-red-500/20 hover:bg-red-500/20 transition-colors text-sm font-medium"
                                                >
                                                    <Trash2 className="w-4 h-4" />
                                                    Vaciar
                                                </button>
                                            )}
                                        </div>
                                    </div>

                                    {/* Schema info en modo Pro */}
                                    {proMode && tableSchema && (
                                        <motion.div
                                            initial={{ height: 0, opacity: 0 }}
                                            animate={{ height: "auto", opacity: 1 }}
                                            className="mt-6 p-4 bg-card-foreground/5 rounded-xl border border-card-border"
                                        >
                                            <p className="text-[10px] font-bold text-sidebar-muted uppercase tracking-wider mb-3 flex items-center gap-2">
                                                <Database className="w-3 h-3" />
                                                Schema de Base de Datos
                                            </p>
                                            <div className="flex flex-wrap gap-2 max-h-32 overflow-y-auto custom-scrollbar">
                                                {tableSchema.columns.map((col) => (
                                                    <div
                                                        key={col.name}
                                                        className={cn(
                                                            "px-2.5 py-1.5 rounded-lg text-xs font-mono border flex items-center gap-2",
                                                            col.primary_key
                                                                ? "bg-amber-500/10 text-amber-500 border-amber-500/20"
                                                                : "bg-card-foreground/5 text-card-foreground/70 border-card-border"
                                                        )}
                                                    >
                                                        <span className="font-bold">{col.name}</span>
                                                        <span className="text-[10px] opacity-50 uppercase tracking-wider">{col.type}</span>
                                                        {col.primary_key && <span className="text-[10px]">🔑PK</span>}
                                                    </div>
                                                ))}
                                            </div>
                                        </motion.div>
                                    )}
                                </div>

                                {/* Tabla de datos */}
                                <div className="overflow-x-auto flex-1 custom-scrollbar">
                                    {loadingData ? (
                                        <div className="flex items-center justify-center h-full min-h-[300px]">
                                            <div className="flex flex-col items-center gap-4">
                                                <Loader2 className="w-8 h-8 animate-spin text-sidebar-accent" />
                                                <span className="text-sm text-sidebar-muted animate-pulse">Cargando datos...</span>
                                            </div>
                                        </div>
                                    ) : (
                                        <table className="w-full text-left border-collapse">
                                            <thead className="bg-card-foreground/5 sticky top-0 z-10 backdrop-blur-md">
                                                <tr>
                                                    {proMode && <th className="px-4 py-3 text-xs font-bold text-sidebar-muted border-b border-white/5 w-20">ACCIONES</th>}
                                                    {visibleColumns.map((col) => (
                                                        <th
                                                            key={col}
                                                            className="px-6 py-3 text-xs font-bold text-sidebar-muted uppercase tracking-wider border-b border-white/5 whitespace-nowrap"
                                                        >
                                                            <div className="flex items-center gap-1">
                                                                {col}
                                                                {tableSchema?.columns.find(c => c.name === col)?.primary_key && (
                                                                    <span className="text-amber-500/50">🔑</span>
                                                                )}
                                                            </div>
                                                        </th>
                                                    ))}
                                                    {!proMode && (tableData?.columns.length || 0) > 6 && (
                                                        <th className="px-4 py-3 text-xs font-bold text-sidebar-muted border-b border-white/5">+Cols</th>
                                                    )}
                                                </tr>
                                            </thead>
                                            <tbody className="divide-y divide-white/5">
                                                {filteredRows.map((row, idx) => (
                                                    <tr
                                                        key={idx}
                                                        className={cn(
                                                            "hover:bg-white/[0.02] transition-colors group",
                                                            editingRow === row.id && "bg-sidebar-accent/5 ring-1 ring-inset ring-sidebar-accent/10"
                                                        )}
                                                    >
                                                        {proMode && (
                                                            <td className="px-4 py-3">
                                                                <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                                                    {editingRow === row.id ? (
                                                                        <>
                                                                            <button
                                                                                onClick={() => updateRow(selectedTable, row.id as number)}
                                                                                className="p-1.5 text-green-400 hover:bg-green-500/20 rounded-lg transition-colors border border-transparent hover:border-green-500/20"
                                                                            >
                                                                                <Check className="w-3.5 h-3.5" />
                                                                            </button>
                                                                            <button
                                                                                onClick={() => { setEditingRow(null); setEditData({}); }}
                                                                                className="p-1.5 text-white/40 hover:text-white hover:bg-white/10 rounded-lg transition-colors"
                                                                            >
                                                                                <X className="w-3.5 h-3.5" />
                                                                            </button>
                                                                        </>
                                                                    ) : (
                                                                        <>
                                                                            <button
                                                                                onClick={() => startEditing(row)}
                                                                                className="p-1.5 text-blue-400 hover:bg-blue-500/20 rounded-lg transition-colors border border-transparent hover:border-blue-500/20"
                                                                            >
                                                                                <Edit2 className="w-3.5 h-3.5" />
                                                                            </button>
                                                                            <button
                                                                                onClick={() => setShowDeleteConfirm({ type: 'row', id: row.id as number })}
                                                                                className="p-1.5 text-red-400 hover:bg-red-500/20 rounded-lg transition-colors border border-transparent hover:border-red-500/20"
                                                                            >
                                                                                <Trash2 className="w-3.5 h-3.5" />
                                                                            </button>
                                                                        </>
                                                                    )}
                                                                </div>
                                                            </td>
                                                        )}
                                                        {visibleColumns.map((col) => (
                                                            <td
                                                                key={col}
                                                                className="px-6 py-3 text-sm text-card-foreground/80 max-w-[250px]"
                                                            >
                                                                {editingRow === row.id && col !== 'id' ? (
                                                                    <input
                                                                        type="text"
                                                                        value={String(editData[col] || '')}
                                                                        onChange={(e) => setEditData({ ...editData, [col]: e.target.value })}
                                                                        className="w-full px-2 py-1 bg-card-foreground/10 border border-card-border rounded text-sm text-card-foreground focus:border-sidebar-accent focus:ring-1 focus:ring-sidebar-accent outline-none"
                                                                    />
                                                                ) : (
                                                                    <span className="truncate block font-mono text-[13px]">
                                                                        {row[col] !== null ? String(row[col]) : <span className="text-card-foreground/20 italic">null</span>}
                                                                    </span>
                                                                )}
                                                            </td>
                                                        ))}
                                                        {!proMode && (tableData?.columns.length || 0) > 6 && (
                                                            <td className="px-4 py-3 text-sm text-white/20">...</td>
                                                        )}
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    )}
                                </div>

                                {/* Paginación */}
                                {tableData && tableData.total > ROWS_PER_PAGE && (
                                    <div className="p-4 border-t border-card-border bg-card-foreground/[0.02] flex items-center justify-between">
                                        <p className="text-xs text-sidebar-muted font-medium uppercase tracking-wider">
                                            {page * ROWS_PER_PAGE + 1} - {Math.min((page + 1) * ROWS_PER_PAGE, tableData.total)} <span className="opacity-50 mx-1">/</span> {tableData.total}
                                        </p>
                                        <div className="flex items-center gap-2">
                                            <button
                                                onClick={() => fetchTableData(selectedTable, (page - 1) * ROWS_PER_PAGE)}
                                                disabled={page === 0}
                                                className="p-2 rounded-lg hover:bg-white/5 disabled:opacity-20 disabled:cursor-not-allowed transition-colors text-white"
                                            >
                                                <ChevronLeft className="w-5 h-5" />
                                            </button>
                                            <span className="text-sm font-bold text-white px-2">
                                                {page + 1}
                                            </span>
                                            <button
                                                onClick={() => fetchTableData(selectedTable, (page + 1) * ROWS_PER_PAGE)}
                                                disabled={page >= totalPages - 1}
                                                className="p-2 rounded-lg hover:bg-white/5 disabled:opacity-20 disabled:cursor-not-allowed transition-colors text-white"
                                            >
                                                <ChevronRight className="w-5 h-5" />
                                            </button>
                                        </div>
                                    </div>
                                )}
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>
            </div>

            {/* Modal de confirmación de eliminación con estilo Dark Glass */}
            <AnimatePresence>
                {showDeleteConfirm && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-[100]"
                        onClick={() => setShowDeleteConfirm(null)}
                    >
                        <motion.div
                            initial={{ scale: 0.9, opacity: 0 }}
                            animate={{ scale: 1, opacity: 1 }}
                            exit={{ scale: 0.9, opacity: 0 }}
                            className="bg-popover border border-card-border rounded-[2rem] p-8 max-w-md w-full mx-4 shadow-2xl relative overflow-hidden"
                            onClick={(e) => e.stopPropagation()}
                        >
                            {/* Background Glow */}
                            <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full h-32 bg-red-500/10 blur-[50px] pointer-events-none" />

                            <div className="flex flex-col items-center text-center gap-4 mb-6 relative z-10">
                                <div className="p-4 bg-red-500/10 rounded-full border border-red-500/20 shadow-[0_0_20px_-5px_rgba(239,68,68,0.4)]">
                                    <AlertTriangle className="w-8 h-8 text-red-500" />
                                </div>
                                <div>
                                    <h3 className="text-xl font-bold text-white mb-1">
                                        {showDeleteConfirm.type === 'row' && '¿Eliminar registro?'}
                                        {showDeleteConfirm.type === 'table' && '¿Vaciar tabla?'}
                                        {showDeleteConfirm.type === 'all' && '⚠️ ZONA DE PELIGRO'}
                                    </h3>
                                    <p className="text-sm text-sidebar-muted">
                                        {showDeleteConfirm.type !== 'all' ? "Esta acción es irreversible" : "Vas a eliminar TODOS los datos del sistema"}
                                    </p>
                                </div>
                            </div>

                            <p className="text-white/80 text-center mb-8 relative z-10 bg-white/5 p-4 rounded-xl border border-white/5 text-sm">
                                {showDeleteConfirm.type === 'row' && `Se eliminará permanentemente el registro #${showDeleteConfirm.id}.`}
                                {showDeleteConfirm.type === 'table' && `Se eliminarán ${tableData?.total} registros de la tabla "${selectedTable}".`}
                                {showDeleteConfirm.type === 'all' && `Se eliminarán TODOS los registros de TODAS las tablas (${tables.reduce((acc, t) => acc + t.row_count, 0)}). El sistema quedará vacío.`}
                            </p>

                            <div className="flex gap-3 relative z-10">
                                <button
                                    onClick={() => setShowDeleteConfirm(null)}
                                    className="flex-1 px-4 py-3 bg-white/5 text-white rounded-xl font-bold hover:bg-white/10 transition-colors border border-white/5"
                                >
                                    Cancelar
                                </button>
                                <button
                                    onClick={() => {
                                        if (showDeleteConfirm.type === 'row' && selectedTable && showDeleteConfirm.id) {
                                            deleteRow(selectedTable, showDeleteConfirm.id);
                                        } else if (showDeleteConfirm.type === 'table' && selectedTable) {
                                            clearTable(selectedTable);
                                        } else if (showDeleteConfirm.type === 'all') {
                                            clearAllData();
                                        }
                                    }}
                                    className="flex-1 px-4 py-3 bg-red-500 text-white rounded-xl font-bold hover:bg-red-600 transition-colors shadow-lg hover:shadow-red-500/30"
                                >
                                    {showDeleteConfirm.type === 'all' ? 'ELIMINAR TODO' : 'Confirmar'}
                                </button>
                            </div>
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Notificaciones */}
            <AnimatePresence>
                {notification && (
                    <motion.div
                        initial={{ opacity: 0, y: 50, scale: 0.9 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        exit={{ opacity: 0, y: 50, scale: 0.9 }}
                        className={cn(
                            "fixed bottom-6 right-6 px-6 py-4 rounded-2xl shadow-2xl flex items-center gap-3 z-50 border",
                            notification.type === 'success'
                                ? "bg-[#18181b]/90 border-green-500/20 text-green-400"
                                : "bg-[#18181b]/90 border-red-500/20 text-red-400"
                        )}
                    >
                        <div className={cn(
                            "p-2 rounded-full",
                            notification.type === 'success' ? "bg-green-500/10" : "bg-red-500/10"
                        )}>
                            {notification.type === 'success' ? <Check className="w-5 h-5" /> : <X className="w-5 h-5" />}
                        </div>
                        <span className="font-medium text-white">{notification.message}</span>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
}
