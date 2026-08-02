import { Button } from './Button'

interface ZoomControlsProps {
  zoomPercent: number
  onZoomIn: () => void
  onZoomOut: () => void
  onReset: () => void
}

export function ZoomControls({ zoomPercent, onZoomIn, onZoomOut, onReset }: ZoomControlsProps) {
  return (
    <div className="absolute bottom-3 right-3 z-10 flex items-center gap-1 bg-white rounded-lg border border-slate-200 shadow-sm px-1.5 py-1">
      <Button variant="ghost" size="sm" onClick={onZoomOut} title="Alejar">−</Button>
      <span className="text-xs text-slate-500 w-10 text-center select-none">{zoomPercent}%</span>
      <Button variant="ghost" size="sm" onClick={onZoomIn} title="Acercar">+</Button>
      <div className="w-px h-4 bg-slate-200 mx-1" />
      <Button variant="ghost" size="sm" onClick={onReset} title="Ajustar a pantalla">⤢</Button>
    </div>
  )
}