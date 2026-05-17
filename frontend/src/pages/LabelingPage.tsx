import { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, CheckCircle } from 'lucide-react'
import { api } from '../api'
import { useAsync } from '../hooks/useAsync'
import { ImageCanvas } from '../components/ImageCanvas'
import { LabelingPanel } from '../components/labeling/LabelingPanel'
import { LabelsManager } from '../components/labeling/LabelsManager'
import { Button } from '../components/Button'
import type { Word, LabelSchema, SegmentedWord, SegmentationMethod } from '../types'

export function LabelingPage() {
  const { projectId, documentId } = useParams<{ projectId: string; documentId: string }>()
  const pid = Number(projectId)
  const did = Number(documentId)
  const navigate = useNavigate()

  const { data: doc } = useAsync(() => api.documents.get(pid, did), [did])
  const imageUrl = api.documents.imageUrl(pid, did)

  const [words, setWords] = useState<Word[]>([])
  const [labels, setLabels] = useState<LabelSchema[]>([])
  const [selectedWordId, setSelectedWordId] = useState<number | null>(null)
  const [drawingMode, setDrawingMode] = useState(false)
  const [previewWords, setPreviewWords] = useState<SegmentedWord[]>([])
  const [segmenting, setSegmenting] = useState(false)

  // Cargar datos iniciales
  useEffect(() => {
    api.words.list(did).then(setWords)
    api.labels.list(pid).then(setLabels)
  }, [did, pid])

  // ─── Atajos de teclado ────────────────────────────────────────────────────
  useEffect(() => {
    function handleKey(e: KeyboardEvent) {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return
      if (!selectedWordId) return
      const label = labels.find(l => l.shortcut === e.key)
      if (label) handleAssignLabel(selectedWordId, label.id)
    }
    window.addEventListener('keydown', handleKey)
    return () => window.removeEventListener('keydown', handleKey)
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedWordId, labels])

  // ─── Nuevo bbox dibujado ──────────────────────────────────────────────────
  const handleNewWord = useCallback(async (x: number, y: number, w: number, h: number) => {
    const newWord = await api.words.create(did, {
      bbox_x: x, bbox_y: y, bbox_width: w, bbox_height: h,
      order_index: words.length,
      source: 'manual',
    })
    setWords(prev => [...prev, newWord])
    setSelectedWordId(newWord.id)
    setDrawingMode(false)
  }, [did, words.length])

  // ─── Mover / redimensionar bbox ───────────────────────────────────────────
  const handleWordMoved = useCallback(async (wordId: number, x: number, y: number, w: number, h: number) => {
    const updated = await api.words.update(did, wordId, {
      bbox_x: x, bbox_y: y, bbox_width: w, bbox_height: h,
    })
    setWords(prev => prev.map(ww => ww.id === wordId ? updated : ww))
  }, [did])

  // ─── Transcripción ────────────────────────────────────────────────────────
  const handleUpdateTranscription = useCallback(async (wordId: number, text: string) => {
    const updated = await api.words.update(did, wordId, { transcription: text })
    setWords(prev => prev.map(ww => ww.id === wordId ? updated : ww))
  }, [did])

  // ─── Etiquetas ────────────────────────────────────────────────────────────
  const handleAssignLabel = useCallback(async (wordId: number, labelId: number) => {
    await api.words.assignLabel(did, wordId, labelId)
    const updated = await api.words.list(did)
    setWords(updated)
  }, [did])

  const handleRemoveLabel = useCallback(async (wordId: number, labelSchemaId: number) => {
    await api.words.removeLabel(did, wordId, labelSchemaId)
    const updated = await api.words.list(did)
    setWords(updated)
  }, [did])

  // ─── Eliminar palabra ─────────────────────────────────────────────────────
  const handleDeleteWord = useCallback(async (wordId: number) => {
    await api.words.delete(did, wordId)
    setWords(prev => prev.filter(w => w.id !== wordId))
    setSelectedWordId(null)
  }, [did])

  // ─── Segmentación asistida ────────────────────────────────────────────────
  const handlePreview = useCallback(async (method: SegmentationMethod) => {
    setSegmenting(true)
    try {
      const result = await api.segmentation.preview(did, method)
      setPreviewWords(result.words)
    } catch (e) {
      alert('Error en la segmentación: ' + (e instanceof Error ? e.message : e))
    } finally {
      setSegmenting(false)
    }
  }, [did])

  const handleApply = useCallback(async (method: SegmentationMethod) => {
    if (!confirm('¿Aplicar segmentación? Las palabras auto existentes serán reemplazadas.')) return
    setSegmenting(true)
    try {
      const result = await api.segmentation.apply(did, method)
      setWords(prev => [...prev.filter(w => w.source === 'manual'), ...result])
      setPreviewWords([])
    } catch (e) {
      alert('Error: ' + (e instanceof Error ? e.message : e))
    } finally {
      setSegmenting(false)
    }
  }, [did])

  // ─── Esquemas de etiquetas ────────────────────────────────────────────────
  const handleAddLabel = useCallback(async (name: string, color: string, shortcut: string) => {
    const created = await api.labels.create(pid, { name, color, shortcut: shortcut || undefined })
    setLabels(prev => [...prev, created])
  }, [pid])

  const handleDeleteLabel = useCallback(async (id: number) => {
    await api.labels.delete(pid, id)
    setLabels(prev => prev.filter(l => l.id !== id))
  }, [pid])

  // ─── Marcar completado ────────────────────────────────────────────────────
  async function markCompleted() {
    await api.documents.updateStatus(pid, did, 'completed')
    navigate(`/projects/${pid}`)
  }

  return (
    <div className="flex flex-col h-screen overflow-hidden">
      {/* Topbar */}
      <div className="bg-white border-b border-slate-200 px-4 py-2.5 flex items-center gap-3 shrink-0">
        <button onClick={() => navigate(`/projects/${pid}`)} className="text-slate-400 hover:text-slate-700">
          <ArrowLeft size={18} />
        </button>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold text-slate-800 truncate">
            {doc?.original_filename ?? '…'}
          </p>
          <p className="text-xs text-slate-400">
            {words.length} palabras · {words.filter(w => w.labels.length > 0).length} etiquetadas
          </p>
        </div>
        <Button size="sm" variant="secondary" onClick={markCompleted}>
          <CheckCircle size={13} /> Marcar completado
        </Button>
      </div>

      {/* Layout principal */}
      <div className="flex flex-1 overflow-hidden">
        {/* Canvas */}
        <ImageCanvas
          imageUrl={imageUrl}
          words={words}
          previewWords={previewWords}
          labels={labels}
          selectedWordId={selectedWordId}
          onSelectWord={setSelectedWordId}
          onWordMoved={handleWordMoved}
          onNewWord={handleNewWord}
          drawingMode={drawingMode}
        />

        {/* Panel derecho */}
        <div className="flex flex-col w-80 overflow-hidden border-l border-slate-200">
          <LabelsManager
            labels={labels}
            onAdd={handleAddLabel}
            onDelete={handleDeleteLabel}
          />
          <LabelingPanel
            words={words}
            labels={labels}
            selectedWordId={selectedWordId}
            onSelectWord={setSelectedWordId}
            onAssignLabel={handleAssignLabel}
            onRemoveLabel={handleRemoveLabel}
            onUpdateTranscription={handleUpdateTranscription}
            onDeleteWord={handleDeleteWord}
            onPreviewSegmentation={handlePreview}
            onApplySegmentation={handleApply}
            segmenting={segmenting}
            previewCount={previewWords.length > 0 ? previewWords.length : null}
            drawingMode={drawingMode}
            onToggleDrawingMode={() => setDrawingMode(d => !d)}
          />
        </div>
      </div>
    </div>
  )
}
