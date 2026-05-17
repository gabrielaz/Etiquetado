import { useState } from 'react'
import { Tag, Wand2, ChevronDown, Check, X, Pencil, Trash2, AlertCircle } from 'lucide-react'
import clsx from 'clsx'
import type { Word, LabelSchema, SegmentationMethod } from '../../types'
import { Button } from '../Button'

interface LabelingPanelProps {
  words: Word[]
  labels: LabelSchema[]
  selectedWordId: number | null
  onSelectWord: (id: number | null) => void
  onAssignLabel: (wordId: number, labelId: number) => void
  onRemoveLabel: (wordId: number, labelId: number) => void
  onUpdateTranscription: (wordId: number, text: string) => void
  onDeleteWord: (wordId: number) => void
  // Segmentación asistida
  onPreviewSegmentation: (method: SegmentationMethod) => void
  onApplySegmentation: (method: SegmentationMethod) => void
  segmenting: boolean
  previewCount: number | null
  drawingMode: boolean
  onToggleDrawingMode: () => void
}

const METHODS: { value: SegmentationMethod; label: string; desc: string }[] = [
  { value: 'contour',    label: 'Contorno',    desc: 'Morfología OpenCV — recomendado' },
  { value: 'projection', label: 'Proyección',  desc: 'Para líneas regulares' },
  { value: 'mser',       label: 'MSER',        desc: 'Fondos complejos' },
]

export function LabelingPanel({
  words, labels, selectedWordId,
  onSelectWord, onAssignLabel, onRemoveLabel,
  onUpdateTranscription, onDeleteWord,
  onPreviewSegmentation, onApplySegmentation,
  segmenting, previewCount, drawingMode, onToggleDrawingMode,
}: LabelingPanelProps) {
  const [method, setMethod] = useState<SegmentationMethod>('contour')
  const [editingId, setEditingId] = useState<number | null>(null)
  const [editText, setEditText] = useState('')

  const selectedWord = words.find(w => w.id === selectedWordId)

  function startEdit(word: Word) {
    setEditingId(word.id)
    setEditText(word.transcription ?? '')
  }

  function saveEdit(wordId: number) {
    onUpdateTranscription(wordId, editText)
    setEditingId(null)
  }

  return (
    <div className="w-80 bg-white border-l border-slate-200 flex flex-col overflow-hidden">

      {/* ── Segmentación asistida ─────────────────────────────────────────── */}
      <div className="p-4 border-b border-slate-100">
        <div className="flex items-center gap-2 mb-3">
          <Wand2 size={15} className="text-amber-500" />
          <span className="text-sm font-semibold text-slate-700">Segmentación asistida</span>
        </div>

        <select
          value={method}
          onChange={e => setMethod(e.target.value as SegmentationMethod)}
          className="w-full text-xs border border-slate-200 rounded-md px-2 py-1.5 mb-2 focus:outline-none focus:ring-1 focus:ring-blue-400"
        >
          {METHODS.map(m => (
            <option key={m.value} value={m.value}>{m.label} — {m.desc}</option>
          ))}
        </select>

        <div className="flex gap-2">
          <Button
            variant="secondary"
            size="sm"
            className="flex-1"
            disabled={segmenting}
            onClick={() => onPreviewSegmentation(method)}
          >
            {segmenting ? 'Analizando…' : 'Previsualizar'}
          </Button>
          <Button
            size="sm"
            className="flex-1"
            disabled={segmenting}
            onClick={() => onApplySegmentation(method)}
          >
            Aplicar
          </Button>
        </div>

        {previewCount !== null && (
          <p className="text-xs text-amber-600 mt-2 flex items-center gap-1">
            <AlertCircle size={11} />
            {previewCount} palabras detectadas (contornos amarillos)
          </p>
        )}
      </div>

      {/* ── Herramienta de dibujo ─────────────────────────────────────────── */}
      <div className="px-4 py-3 border-b border-slate-100">
        <button
          onClick={onToggleDrawingMode}
          className={clsx(
            'w-full text-xs font-medium px-3 py-2 rounded-lg border transition-colors flex items-center justify-center gap-1.5',
            drawingMode
              ? 'bg-blue-600 text-white border-blue-600'
              : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
          )}
        >
          <Pencil size={12} />
          {drawingMode ? 'Modo dibujo ACTIVO — clic para desactivar' : 'Activar modo dibujo'}
        </button>
      </div>

      {/* ── Palabra seleccionada ──────────────────────────────────────────── */}
      {selectedWord && (
        <div className="p-4 border-b border-slate-100 bg-blue-50">
          <div className="flex items-start justify-between mb-2">
            <span className="text-xs font-semibold text-blue-700 uppercase tracking-wide">
              Palabra #{selectedWord.order_index + 1}
            </span>
            <button
              onClick={() => onDeleteWord(selectedWord.id)}
              className="text-slate-400 hover:text-red-500 transition-colors"
            >
              <Trash2 size={13} />
            </button>
          </div>

          {/* Transcripción */}
          {editingId === selectedWord.id ? (
            <div className="flex gap-1 mb-2">
              <input
                autoFocus
                value={editText}
                onChange={e => setEditText(e.target.value)}
                onKeyDown={e => {
                  if (e.key === 'Enter') saveEdit(selectedWord.id)
                  if (e.key === 'Escape') setEditingId(null)
                }}
                className="flex-1 border border-blue-300 rounded px-2 py-1 text-xs focus:outline-none"
              />
              <button onClick={() => saveEdit(selectedWord.id)} className="text-green-600 hover:text-green-700">
                <Check size={14} />
              </button>
              <button onClick={() => setEditingId(null)} className="text-slate-400 hover:text-slate-600">
                <X size={14} />
              </button>
            </div>
          ) : (
            <div
              className="flex items-center gap-1.5 mb-2 cursor-pointer group"
              onClick={() => startEdit(selectedWord)}
            >
              <span className={clsx(
                'text-sm flex-1',
                selectedWord.transcription ? 'text-slate-800 font-medium' : 'text-slate-400 italic'
              )}>
                {selectedWord.transcription || 'Sin transcripción — clic para editar'}
              </span>
              <Pencil size={11} className="text-slate-300 group-hover:text-blue-500 shrink-0" />
            </div>
          )}

          {/* Etiquetas asignadas */}
          <div className="flex flex-wrap gap-1 mb-2">
            {selectedWord.labels.map(wl => (
              <span
                key={wl.id}
                className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full text-white font-medium"
                style={{ backgroundColor: wl.label_color ?? '#6b7280' }}
              >
                {wl.label_name}
                <button onClick={() => onRemoveLabel(selectedWord.id, wl.label_schema_id)}>
                  <X size={10} />
                </button>
              </span>
            ))}
          </div>

          {/* Asignar etiquetas */}
          <div className="flex flex-wrap gap-1">
            {labels
              .filter(l => !selectedWord.labels.find(wl => wl.label_schema_id === l.id))
              .map(l => (
                <button
                  key={l.id}
                  onClick={() => onAssignLabel(selectedWord.id, l.id)}
                  className="text-xs px-2 py-0.5 rounded-full border font-medium transition-colors hover:opacity-80"
                  style={{ borderColor: l.color, color: l.color }}
                  title={l.shortcut ? `Atajo: ${l.shortcut}` : undefined}
                >
                  {l.name}{l.shortcut && <span className="opacity-50 ml-1">[{l.shortcut}]</span>}
                </button>
              ))}
          </div>

          {/* Confianza segmentación */}
          {selectedWord.confidence !== null && (
            <p className="text-xs text-slate-400 mt-2">
              Confianza: {Math.round((selectedWord.confidence ?? 0) * 100)}% · {selectedWord.source}
            </p>
          )}
        </div>
      )}

      {/* ── Lista de palabras ─────────────────────────────────────────────── */}
      <div className="flex-1 overflow-y-auto">
        <div className="px-4 py-2 flex items-center gap-2 sticky top-0 bg-white border-b border-slate-100 z-10">
          <Tag size={13} className="text-slate-400" />
          <span className="text-xs font-semibold text-slate-600 uppercase tracking-wide">
            Palabras ({words.length})
          </span>
        </div>

        {words.length === 0 && (
          <div className="text-center py-8 text-slate-400 text-xs">
            Dibuja o segmenta para agregar palabras
          </div>
        )}

        <div className="divide-y divide-slate-50">
          {words.map((word) => (
            <div
              key={word.id}
              onClick={() => onSelectWord(word.id === selectedWordId ? null : word.id)}
              className={clsx(
                'px-4 py-2.5 cursor-pointer hover:bg-slate-50 transition-colors',
                word.id === selectedWordId && 'bg-blue-50 border-l-2 border-blue-500'
              )}
            >
              <div className="flex items-center gap-2">
                <span className="text-xs text-slate-400 w-5 shrink-0">{word.order_index + 1}</span>
                <span className={clsx(
                  'text-sm flex-1 truncate',
                  word.transcription ? 'text-slate-800' : 'text-slate-300 italic'
                )}>
                  {word.transcription || '—'}
                </span>
                <div className="flex gap-0.5">
                  {word.labels.map(wl => (
                    <span
                      key={wl.id}
                      className="w-2 h-2 rounded-full"
                      style={{ backgroundColor: wl.label_color ?? '#6b7280' }}
                      title={wl.label_name ?? ''}
                    />
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
