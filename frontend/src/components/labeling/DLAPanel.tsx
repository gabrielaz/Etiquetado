import { useState } from 'react'
import { Plus, Trash2, Pencil, X, Check, StickyNote, LayoutTemplate } from 'lucide-react'
import clsx from 'clsx'
import type { LayoutRegion, LayoutRegionType } from '../../types'
import { Button } from '../Button'
import { Modal } from '../Modal'

interface DLAPanelProps {
  regions: LayoutRegion[]
  regionTypes: LayoutRegionType[]
  selectedRegionId: number | null
  onSelectRegion: (id: number | null) => void
  onAssignType: (regionId: number, typeId: number | null) => void
  onUpdateNotes: (regionId: number, notes: string) => void
  onDeleteRegion: (regionId: number) => void
  onAddType: (name: string, color: string, shortcut: string) => void
  onDeleteType: (typeId: number) => void
  onSeedDefaults: () => void
  drawingMode: boolean
  onToggleDrawingMode: () => void
}

const PRESET_COLORS = [
  '#3B82F6','#EF4444','#10B981','#F59E0B',
  '#8B5CF6','#EC4899','#6366F1','#84CC16',
]

export function DLAPanel({
  regions, regionTypes, selectedRegionId,
  onSelectRegion, onAssignType, onUpdateNotes, onDeleteRegion,
  onAddType, onDeleteType, onSeedDefaults,
  drawingMode, onToggleDrawingMode,
}: DLAPanelProps) {
  const [showAddType, setShowAddType] = useState(false)
  const [newName, setNewName] = useState('')
  const [newColor, setNewColor] = useState(PRESET_COLORS[0])
  const [newShortcut, setNewShortcut] = useState('')
  const [editingNotes, setEditingNotes] = useState<number | null>(null)
  const [notesText, setNotesText] = useState('')

  const selectedRegion = regions.find(r => r.id === selectedRegionId)

  function handleAddType(e: React.FormEvent) {
    e.preventDefault()
    if (!newName.trim()) return
    onAddType(newName.trim(), newColor, newShortcut.trim())
    setNewName(''); setNewShortcut(''); setShowAddType(false)
  }

  function startEditNotes(region: LayoutRegion) {
    setEditingNotes(region.id)
    setNotesText(region.notes ?? '')
  }

  function saveNotes(regionId: number) {
    onUpdateNotes(regionId, notesText)
    setEditingNotes(null)
  }

  return (
    <div className="w-80 bg-white border-l border-slate-200 flex flex-col overflow-hidden">

      {/* ── Herramienta de dibujo ──────────────────────────────────────────── */}
      <div className="px-4 py-3 border-b border-slate-100">
        <button
          onClick={onToggleDrawingMode}
          className={clsx(
            'w-full text-xs font-medium px-3 py-2 rounded-lg border transition-colors flex items-center justify-center gap-1.5',
            drawingMode
              ? 'bg-indigo-600 text-white border-indigo-600'
              : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
          )}
        >
          <LayoutTemplate size={13} />
          {drawingMode ? 'Modo dibujo ACTIVO — clic para desactivar' : 'Activar modo dibujo de región'}
        </button>
      </div>

      {/* ── Tipos de región ────────────────────────────────────────────────── */}
      <div className="p-4 border-b border-slate-100">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-semibold text-slate-600 uppercase tracking-wide flex items-center gap-1">
            <LayoutTemplate size={12} /> Tipos de región
          </span>
          <div className="flex gap-1.5">
            {regionTypes.length === 0 && (
              <button
                onClick={onSeedDefaults}
                className="text-xs text-indigo-600 hover:text-indigo-700 font-medium"
                title="Cargar tipos predefinidos"
              >
                Predefinidos
              </button>
            )}
            <button onClick={() => setShowAddType(true)} className="text-indigo-600 hover:text-indigo-700">
              <Plus size={15} />
            </button>
          </div>
        </div>
        <div className="flex flex-wrap gap-1.5">
          {regionTypes.map(rt => (
            <div
              key={rt.id}
              className="group flex items-center gap-1 text-xs px-2 py-0.5 rounded-full text-white font-medium"
              style={{ backgroundColor: rt.color }}
            >
              <span>{rt.name}</span>
              {rt.shortcut && <span className="opacity-60">[{rt.shortcut}]</span>}
              <button
                onClick={() => onDeleteType(rt.id)}
                className="opacity-0 group-hover:opacity-100 transition-opacity ml-0.5"
              >
                <Trash2 size={10} />
              </button>
            </div>
          ))}
          {regionTypes.length === 0 && (
            <p className="text-xs text-slate-400">Sin tipos — añade uno o carga los predefinidos</p>
          )}
        </div>
      </div>

      {/* ── Región seleccionada ────────────────────────────────────────────── */}
      {selectedRegion && (
        <div className="p-4 border-b border-slate-100 bg-indigo-50">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-semibold text-indigo-700 uppercase tracking-wide">
              Región #{selectedRegion.order_index + 1}
            </span>
            <button
              onClick={() => onDeleteRegion(selectedRegion.id)}
              className="text-slate-400 hover:text-red-500 transition-colors"
            >
              <Trash2 size={13} />
            </button>
          </div>

          {/* Asignar tipo */}
          <div className="mb-3">
            <label className="block text-xs text-slate-500 mb-1 font-medium">Tipo de región</label>
            <div className="flex flex-wrap gap-1">
              <button
                onClick={() => onAssignType(selectedRegion.id, null)}
                className={clsx(
                  'text-xs px-2 py-0.5 rounded-full border transition-colors',
                  !selectedRegion.region_type_id
                    ? 'bg-slate-200 border-slate-400 text-slate-700'
                    : 'border-slate-200 text-slate-400 hover:bg-slate-50'
                )}
              >
                Sin tipo
              </button>
              {regionTypes.map(rt => (
                <button
                  key={rt.id}
                  onClick={() => onAssignType(selectedRegion.id, rt.id)}
                  className={clsx(
                    'text-xs px-2 py-0.5 rounded-full border font-medium transition-all',
                    selectedRegion.region_type_id === rt.id
                      ? 'text-white'
                      : 'hover:opacity-80'
                  )}
                  style={
                    selectedRegion.region_type_id === rt.id
                      ? { backgroundColor: rt.color, borderColor: rt.color }
                      : { borderColor: rt.color, color: rt.color }
                  }
                  title={rt.shortcut ? `Atajo: ${rt.shortcut}` : undefined}
                >
                  {rt.name}
                  {rt.shortcut && <span className="opacity-60 ml-1">[{rt.shortcut}]</span>}
                </button>
              ))}
            </div>
          </div>

          {/* Notas */}
          <div>
            <label className="block text-xs text-slate-500 mb-1 font-medium flex items-center gap-1">
              <StickyNote size={11} /> Notas
            </label>
            {editingNotes === selectedRegion.id ? (
              <div className="flex flex-col gap-1">
                <textarea
                  autoFocus
                  value={notesText}
                  onChange={e => setNotesText(e.target.value)}
                  rows={2}
                  className="w-full border border-indigo-300 rounded px-2 py-1 text-xs resize-none focus:outline-none"
                />
                <div className="flex gap-1 justify-end">
                  <button onClick={() => saveNotes(selectedRegion.id)} className="text-green-600 hover:text-green-700">
                    <Check size={14} />
                  </button>
                  <button onClick={() => setEditingNotes(null)} className="text-slate-400 hover:text-slate-600">
                    <X size={14} />
                  </button>
                </div>
              </div>
            ) : (
              <div
                onClick={() => startEditNotes(selectedRegion)}
                className="text-xs text-slate-500 cursor-pointer hover:text-slate-700 italic flex items-start gap-1 group"
              >
                <span className="flex-1">{selectedRegion.notes || 'Añadir nota…'}</span>
                <Pencil size={10} className="opacity-0 group-hover:opacity-100 mt-0.5 shrink-0 text-indigo-400" />
              </div>
            )}
          </div>

          {/* Dimensiones */}
          <p className="text-xs text-slate-400 mt-2">
            {Math.round(selectedRegion.bbox_width)} × {Math.round(selectedRegion.bbox_height)} px
          </p>
        </div>
      )}

      {/* ── Lista de regiones ──────────────────────────────────────────────── */}
      <div className="flex-1 overflow-y-auto">
        <div className="px-4 py-2 flex items-center gap-2 sticky top-0 bg-white border-b border-slate-100 z-10">
          <LayoutTemplate size={13} className="text-slate-400" />
          <span className="text-xs font-semibold text-slate-600 uppercase tracking-wide">
            Regiones ({regions.length})
          </span>
        </div>

        {regions.length === 0 && (
          <div className="text-center py-8 text-slate-400 text-xs px-4">
            Activa el modo dibujo y marca las regiones sobre la imagen
          </div>
        )}

        <div className="divide-y divide-slate-50">
          {regions.map(region => (
            <div
              key={region.id}
              onClick={() => onSelectRegion(region.id === selectedRegionId ? null : region.id)}
              className={clsx(
                'px-4 py-2.5 cursor-pointer hover:bg-slate-50 transition-colors',
                region.id === selectedRegionId && 'bg-indigo-50 border-l-2 border-indigo-500'
              )}
            >
              <div className="flex items-center gap-2">
                <span className="text-xs text-slate-400 w-5 shrink-0">{region.order_index + 1}</span>
                {region.type_color && (
                  <span
                    className="w-2.5 h-2.5 rounded-sm shrink-0"
                    style={{ backgroundColor: region.type_color }}
                  />
                )}
                <span className={clsx(
                  'text-sm flex-1 truncate',
                  region.type_name ? 'text-slate-800 font-medium' : 'text-slate-400 italic'
                )}>
                  {region.type_name ?? 'Sin tipo'}
                </span>
                <span className="text-xs text-slate-400 shrink-0">
                  {Math.round(region.bbox_width)}×{Math.round(region.bbox_height)}
                </span>
              </div>
              {region.notes && (
                <p className="text-xs text-slate-400 truncate ml-7 mt-0.5">{region.notes}</p>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Modal: nuevo tipo */}
      {showAddType && (
        <Modal title="Nuevo tipo de región" onClose={() => setShowAddType(false)}>
          <form onSubmit={handleAddType} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Nombre *</label>
              <input
                autoFocus
                value={newName}
                onChange={e => setNewName(e.target.value)}
                placeholder="ej: Texto principal, Nota al margen…"
                className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Color</label>
              <div className="flex gap-2 flex-wrap">
                {PRESET_COLORS.map(c => (
                  <button
                    key={c} type="button" onClick={() => setNewColor(c)}
                    className="w-7 h-7 rounded-full border-2 transition-transform hover:scale-110"
                    style={{ backgroundColor: c, borderColor: newColor === c ? '#1e293b' : 'transparent' }}
                  />
                ))}
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Atajo de teclado</label>
              <input
                value={newShortcut}
                onChange={e => setNewShortcut(e.target.value.slice(0, 2))}
                placeholder="ej: t, n, f"
                maxLength={2}
                className="w-24 border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
              />
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <Button variant="secondary" type="button" onClick={() => setShowAddType(false)}>Cancelar</Button>
              <Button type="submit" disabled={!newName.trim()}>Crear tipo</Button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  )
}
