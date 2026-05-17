import { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, Tag } from 'lucide-react'
import { api } from '../api'
import { useAsync } from '../hooks/useAsync'
import { DLACanvas } from '../components/DLACanvas'
import { DLAPanel } from '../components/labeling/DLAPanel'
import { Button } from '../components/Button'
import type { LayoutRegion, LayoutRegionType } from '../types'

export function DLAPage() {
  const { projectId, documentId } = useParams<{ projectId: string; documentId: string }>()
  const pid = Number(projectId)
  const did = Number(documentId)
  const navigate = useNavigate()

  const { data: doc } = useAsync(() => api.documents.get(pid, did), [did])
  const imageUrl = api.documents.imageUrl(pid, did)

  const [regions, setRegions] = useState<LayoutRegion[]>([])
  const [regionTypes, setRegionTypes] = useState<LayoutRegionType[]>([])
  const [selectedRegionId, setSelectedRegionId] = useState<number | null>(null)
  const [drawingMode, setDrawingMode] = useState(false)

  useEffect(() => {
    api.layoutRegions.list(did).then(setRegions)
    api.layoutTypes.list(pid).then(setRegionTypes)
  }, [did, pid])

  // ─── Asignar tipo ─────────────────────────────────────────────────────────
  const handleAssignType = useCallback(async (regionId: number, typeId: number | null) => {
    const updated = await api.layoutRegions.update(did, regionId, { region_type_id: typeId })
    setRegions(prev => prev.map(r => r.id === regionId ? updated : r))
  }, [did])

  // ─── Nueva región dibujada ────────────────────────────────────────────────
  const handleNewRegion = useCallback(async (x: number, y: number, w: number, h: number) => {
    const region = await api.layoutRegions.create(did, {
      bbox_x: x, bbox_y: y, bbox_width: w, bbox_height: h,
      order_index: regions.length,
    })
    setRegions(prev => [...prev, region])
    setSelectedRegionId(region.id)
    setDrawingMode(false)
  }, [did, regions.length])

  // ─── Mover / redimensionar ────────────────────────────────────────────────
  const handleRegionMoved = useCallback(async (id: number, x: number, y: number, w: number, h: number) => {
    const updated = await api.layoutRegions.update(did, id, {
      bbox_x: x, bbox_y: y, bbox_width: w, bbox_height: h,
    })
    setRegions(prev => prev.map(r => r.id === id ? updated : r))
  }, [did])

  // ─── Atajos de teclado ────────────────────────────────────────────────────
  useEffect(() => {
    function handleKey(e: KeyboardEvent) {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return
      if (!selectedRegionId) return
      const rt = regionTypes.find(t => t.shortcut === e.key)
      if (rt) handleAssignType(selectedRegionId, rt.id)
    }
    window.addEventListener('keydown', handleKey)
    return () => window.removeEventListener('keydown', handleKey)
  }, [selectedRegionId, regionTypes, handleAssignType])

  // ─── Notas ────────────────────────────────────────────────────────────────
  const handleUpdateNotes = useCallback(async (regionId: number, notes: string) => {
    const updated = await api.layoutRegions.update(did, regionId, { notes })
    setRegions(prev => prev.map(r => r.id === regionId ? updated : r))
  }, [did])

  // ─── Eliminar región ──────────────────────────────────────────────────────
  const handleDeleteRegion = useCallback(async (regionId: number) => {
    await api.layoutRegions.delete(did, regionId)
    setRegions(prev => prev.filter(r => r.id !== regionId))
    setSelectedRegionId(null)
  }, [did])

  // ─── Tipos de región ──────────────────────────────────────────────────────
  const handleAddType = useCallback(async (name: string, color: string, shortcut: string) => {
    const created = await api.layoutTypes.create(pid, { name, color, shortcut: shortcut || undefined })
    setRegionTypes(prev => [...prev, created])
  }, [pid])

  const handleDeleteType = useCallback(async (typeId: number) => {
    await api.layoutTypes.delete(pid, typeId)
    setRegionTypes(prev => prev.filter(t => t.id !== typeId))
    // Limpiar tipo en regiones afectadas
    setRegions(prev => prev.map(r =>
      r.region_type_id === typeId ? { ...r, region_type_id: null, type_name: null, type_color: null } : r
    ))
  }, [pid])

  const handleSeedDefaults = useCallback(async () => {
    const created = await api.layoutTypes.seedDefaults(pid)
    setRegionTypes(prev => [...prev, ...created])
  }, [pid])

  return (
    <div className="flex flex-col h-screen overflow-hidden">
      {/* Topbar */}
      <div className="bg-white border-b border-slate-200 px-4 py-2.5 flex items-center gap-3 shrink-0">
        <button onClick={() => navigate(`/projects/${pid}`)} className="text-slate-400 hover:text-slate-700">
          <ArrowLeft size={18} />
        </button>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold text-slate-800 truncate">
            DLA — {doc?.original_filename ?? '…'}
          </p>
          <p className="text-xs text-slate-400">
            {regions.length} región{regions.length !== 1 ? 'es' : ''} anotada{regions.length !== 1 ? 's' : ''}
          </p>
        </div>
        <Button
          size="sm"
          variant="secondary"
          onClick={() => navigate(`/projects/${pid}/documents/${did}/label`)}
        >
          <Tag size={13} /> Ir a Etiquetado
        </Button>
      </div>

      {/* Layout */}
      <div className="flex flex-1 overflow-hidden">
        <DLACanvas
          imageUrl={imageUrl}
          regions={regions}
          selectedRegionId={selectedRegionId}
          onSelectRegion={setSelectedRegionId}
          onRegionMoved={handleRegionMoved}
          onNewRegion={handleNewRegion}
          drawingMode={drawingMode}
        />
        <DLAPanel
          regions={regions}
          regionTypes={regionTypes}
          selectedRegionId={selectedRegionId}
          onSelectRegion={setSelectedRegionId}
          onAssignType={handleAssignType}
          onUpdateNotes={handleUpdateNotes}
          onDeleteRegion={handleDeleteRegion}
          onAddType={handleAddType}
          onDeleteType={handleDeleteType}
          onSeedDefaults={handleSeedDefaults}
          drawingMode={drawingMode}
          onToggleDrawingMode={() => setDrawingMode(d => !d)}
        />
      </div>
    </div>
  )
}
