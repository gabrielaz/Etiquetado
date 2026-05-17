import { useState, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Upload, ArrowLeft, FileImage, CheckCircle, Clock, Tag, Trash2, LayoutTemplate } from 'lucide-react'
import clsx from 'clsx'
import { api } from '../api'
import { useAsync } from '../hooks/useAsync'
import { Button } from '../components/Button'
import type { Document } from '../types'

const STATUS_LABELS: Record<string, { label: string; icon: typeof Clock; color: string }> = {
  pending:     { label: 'Pendiente',    icon: Clock,         color: 'text-slate-500 bg-slate-50 border-slate-200' },
  in_progress: { label: 'En progreso',  icon: Clock,         color: 'text-amber-600 bg-amber-50 border-amber-200' },
  completed:   { label: 'Completado',   icon: CheckCircle,   color: 'text-green-600 bg-green-50 border-green-200' },
}

export function DocumentsPage() {
  const { projectId } = useParams<{ projectId: string }>()
  const pid = Number(projectId)
  const navigate = useNavigate()

  const { data: project } = useAsync(() => api.projects.get(pid), [pid])
  const { data: docs, loading, refetch } = useAsync(() => api.documents.list(pid), [pid])

  const [uploading, setUploading] = useState(false)
  const fileRef = useRef<HTMLInputElement>(null)

  async function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const files = Array.from(e.target.files || [])
    if (!files.length) return
    setUploading(true)
    try {
      await Promise.all(files.map(f => api.documents.upload(pid, f)))
      refetch()
    } finally {
      setUploading(false)
      if (fileRef.current) fileRef.current.value = ''
    }
  }

  async function handleDelete(doc: Document, e: React.MouseEvent) {
    e.stopPropagation()
    if (!confirm(`¿Eliminar "${doc.original_filename}"?`)) return
    await api.documents.delete(pid, doc.id)
    refetch()
  }

  return (
    <div className="max-w-5xl mx-auto px-6 py-8">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <button onClick={() => navigate('/')} className="text-slate-400 hover:text-slate-700 transition-colors">
          <ArrowLeft size={20} />
        </button>
        <div className="flex-1">
          <h1 className="text-2xl font-bold text-slate-800">{project?.name ?? '…'}</h1>
          <p className="text-slate-500 text-sm">{project?.description ?? 'Documentos del proyecto'}</p>
        </div>
        <input
          ref={fileRef}
          type="file"
          accept="image/*,.pdf"
          multiple
          className="hidden"
          onChange={handleFileChange}
        />
        <Button onClick={() => fileRef.current?.click()} disabled={uploading}>
          <Upload size={15} />
          {uploading ? 'Subiendo…' : 'Subir imágenes'}
        </Button>
      </div>

      {loading && <div className="text-center py-16 text-slate-400">Cargando documentos…</div>}

      {!loading && docs?.length === 0 && (
        <div className="text-center py-20 text-slate-400">
          <FileImage size={48} className="mx-auto mb-3 opacity-30" />
          <p className="font-medium">No hay documentos</p>
          <p className="text-sm">Sube imágenes de documentos manuscritos para comenzar</p>
        </div>
      )}

      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {docs?.map(doc => {
          const st = STATUS_LABELS[doc.status]
          const progress = doc.word_count > 0
            ? Math.round((doc.labeled_count / doc.word_count) * 100)
            : 0
          return (
            <div
              key={doc.id}
              onClick={() => navigate(`/projects/${pid}/documents/${doc.id}/label`)}
              className="bg-white border border-slate-200 rounded-xl overflow-hidden cursor-pointer hover:border-blue-300 hover:shadow-md transition-all group"
            >
              {/* Miniatura */}
              <div className="h-36 bg-slate-50 flex items-center justify-center overflow-hidden border-b border-slate-100">
                <img
                  src={api.documents.imageUrl(pid, doc.id)}
                  alt={doc.original_filename}
                  className="max-h-full max-w-full object-contain"
                  onError={e => { (e.target as HTMLImageElement).style.display = 'none' }}
                />
              </div>
              <div className="p-4">
                <p className="font-medium text-slate-800 text-sm truncate mb-2" title={doc.original_filename}>
                  {doc.original_filename}
                </p>

                {/* Estado */}
                <span className={clsx(
                  'inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full border font-medium mb-3',
                  st.color
                )}>
                  <st.icon size={10} />
                  {st.label}
                </span>

                {/* Progreso */}
                {doc.word_count > 0 && (
                  <div>
                    <div className="flex justify-between text-xs text-slate-500 mb-1">
                      <span className="flex items-center gap-1"><Tag size={10} /> {doc.labeled_count}/{doc.word_count} palabras</span>
                      <span>{progress}%</span>
                    </div>
                    <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-blue-500 rounded-full transition-all"
                        style={{ width: `${progress}%` }}
                      />
                    </div>
                  </div>
                )}

                <div className="mt-3 flex items-center justify-between">
                  <div className="flex gap-1.5">
                    <button
                      onClick={e => { e.stopPropagation(); navigate(`/projects/${pid}/documents/${doc.id}/label`) }}
                      className="flex items-center gap-1 text-xs px-2 py-1 rounded-md bg-blue-50 text-blue-600 hover:bg-blue-100 transition-colors font-medium"
                    >
                      <Tag size={11} /> Etiquetar
                    </button>
                    <button
                      onClick={e => { e.stopPropagation(); navigate(`/projects/${pid}/documents/${doc.id}/dla`) }}
                      className="flex items-center gap-1 text-xs px-2 py-1 rounded-md bg-indigo-50 text-indigo-600 hover:bg-indigo-100 transition-colors font-medium"
                    >
                      <LayoutTemplate size={11} /> DLA
                    </button>
                  </div>
                  <button
                    onClick={e => handleDelete(doc, e)}
                    className="opacity-0 group-hover:opacity-100 p-1.5 rounded-md text-slate-400 hover:text-red-500 hover:bg-red-50 transition-all"
                  >
                    <Trash2 size={13} />
                  </button>
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
