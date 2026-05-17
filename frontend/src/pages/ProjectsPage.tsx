import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Plus, FolderOpen, Trash2, ChevronRight, FileText } from 'lucide-react'
import { api } from '../api'
import { useAsync } from '../hooks/useAsync'
import { Button } from '../components/Button'
import { Modal } from '../components/Modal'
import type { Project } from '../types'

export function ProjectsPage() {
  const navigate = useNavigate()
  const { data: projects, loading, error, refetch } = useAsync(() => api.projects.list())
  const [showModal, setShowModal] = useState(false)
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [saving, setSaving] = useState(false)

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault()
    if (!name.trim()) return
    setSaving(true)
    try {
      await api.projects.create({ name: name.trim(), description: description.trim() || undefined })
      setShowModal(false)
      setName('')
      setDescription('')
      refetch()
    } finally {
      setSaving(false)
    }
  }

  async function handleDelete(p: Project, e: React.MouseEvent) {
    e.stopPropagation()
    if (!confirm(`¿Eliminar el proyecto "${p.name}"?`)) return
    await api.projects.delete(p.id)
    refetch()
  }

  return (
    <div className="max-w-4xl mx-auto px-6 py-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Proyectos</h1>
          <p className="text-slate-500 text-sm mt-0.5">Gestiona tus colecciones de documentos manuscritos</p>
        </div>
        <Button onClick={() => setShowModal(true)}>
          <Plus size={16} /> Nuevo proyecto
        </Button>
      </div>

      {loading && (
        <div className="text-center py-16 text-slate-400">Cargando proyectos…</div>
      )}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg p-4 text-sm">{error}</div>
      )}

      {!loading && projects?.length === 0 && (
        <div className="text-center py-20 text-slate-400">
          <FolderOpen size={48} className="mx-auto mb-3 opacity-30" />
          <p className="font-medium">No hay proyectos aún</p>
          <p className="text-sm">Crea tu primer proyecto para comenzar</p>
        </div>
      )}

      <div className="grid gap-3">
        {projects?.map(p => (
          <div
            key={p.id}
            onClick={() => navigate(`/projects/${p.id}`)}
            className="bg-white border border-slate-200 rounded-xl px-6 py-4 flex items-center gap-4 cursor-pointer hover:border-blue-300 hover:shadow-sm transition-all group"
          >
            <div className="bg-blue-50 rounded-lg p-2.5">
              <FolderOpen size={20} className="text-blue-600" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="font-semibold text-slate-800 truncate">{p.name}</p>
              {p.description && (
                <p className="text-xs text-slate-500 truncate mt-0.5">{p.description}</p>
              )}
            </div>
            <div className="flex items-center gap-4 shrink-0">
              <div className="flex items-center gap-1.5 text-xs text-slate-500">
                <FileText size={13} />
                <span>{p.document_count} doc{p.document_count !== 1 ? 's' : ''}</span>
              </div>
              <button
                onClick={(e) => handleDelete(p, e)}
                className="opacity-0 group-hover:opacity-100 p-1.5 rounded-md text-slate-400 hover:text-red-500 hover:bg-red-50 transition-all"
              >
                <Trash2 size={14} />
              </button>
              <ChevronRight size={16} className="text-slate-300 group-hover:text-blue-400 transition-colors" />
            </div>
          </div>
        ))}
      </div>

      {showModal && (
        <Modal title="Nuevo proyecto" onClose={() => setShowModal(false)}>
          <form onSubmit={handleCreate} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Nombre *</label>
              <input
                autoFocus
                value={name}
                onChange={e => setName(e.target.value)}
                placeholder="ej: Cartas del siglo XIX"
                className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Descripción</label>
              <textarea
                value={description}
                onChange={e => setDescription(e.target.value)}
                rows={2}
                placeholder="Descripción opcional"
                className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400 resize-none"
              />
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <Button variant="secondary" type="button" onClick={() => setShowModal(false)}>Cancelar</Button>
              <Button type="submit" disabled={saving || !name.trim()}>
                {saving ? 'Creando…' : 'Crear proyecto'}
              </Button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  )
}
