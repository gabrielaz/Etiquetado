import { useState } from 'react'
import { Plus, Trash2, Tag } from 'lucide-react'
import type { LabelSchema } from '../../types'
import { Button } from '../Button'
import { Modal } from '../Modal'

interface LabelsManagerProps {
  labels: LabelSchema[]
  onAdd: (name: string, color: string, shortcut: string) => void
  onDelete: (id: number) => void
}

const PRESET_COLORS = [
  '#3B82F6','#EF4444','#10B981','#F59E0B',
  '#8B5CF6','#EC4899','#06B6D4','#84CC16',
]

export function LabelsManager({ labels, onAdd, onDelete }: LabelsManagerProps) {
  const [show, setShow] = useState(false)
  const [name, setName] = useState('')
  const [color, setColor] = useState(PRESET_COLORS[0])
  const [shortcut, setShortcut] = useState('')

  function handleAdd(e: React.FormEvent) {
    e.preventDefault()
    if (!name.trim()) return
    onAdd(name.trim(), color, shortcut.trim())
    setName('')
    setShortcut('')
    setShow(false)
  }

  return (
    <>
      <div className="p-4 border-b border-slate-100">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-600 uppercase tracking-wide">
            <Tag size={12} />
            Etiquetas del proyecto
          </div>
          <button
            onClick={() => setShow(true)}
            className="text-blue-600 hover:text-blue-700"
          >
            <Plus size={15} />
          </button>
        </div>
        <div className="flex flex-wrap gap-1.5">
          {labels.map(l => (
            <div key={l.id} className="group flex items-center gap-1 text-xs px-2 py-0.5 rounded-full text-white font-medium" style={{ backgroundColor: l.color }}>
              <span>{l.name}</span>
              {l.shortcut && <span className="opacity-60">[{l.shortcut}]</span>}
              <button
                onClick={() => onDelete(l.id)}
                className="opacity-0 group-hover:opacity-100 transition-opacity ml-0.5"
              >
                <Trash2 size={10} />
              </button>
            </div>
          ))}
          {labels.length === 0 && (
            <p className="text-xs text-slate-400">Sin etiquetas — añade una</p>
          )}
        </div>
      </div>

      {show && (
        <Modal title="Nueva etiqueta" onClose={() => setShow(false)}>
          <form onSubmit={handleAdd} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Nombre *</label>
              <input
                autoFocus
                value={name}
                onChange={e => setName(e.target.value)}
                placeholder="ej: nombre, fecha, lugar…"
                className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Color</label>
              <div className="flex gap-2 flex-wrap">
                {PRESET_COLORS.map(c => (
                  <button
                    key={c}
                    type="button"
                    onClick={() => setColor(c)}
                    className="w-7 h-7 rounded-full border-2 transition-transform hover:scale-110"
                    style={{
                      backgroundColor: c,
                      borderColor: color === c ? '#1e293b' : 'transparent',
                    }}
                  />
                ))}
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Atajo de teclado</label>
              <input
                value={shortcut}
                onChange={e => setShortcut(e.target.value.slice(0, 2))}
                placeholder="ej: n, f, l"
                maxLength={2}
                className="w-24 border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
              />
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <Button variant="secondary" type="button" onClick={() => setShow(false)}>Cancelar</Button>
              <Button type="submit" disabled={!name.trim()}>Crear etiqueta</Button>
            </div>
          </form>
        </Modal>
      )}
    </>
  )
}
