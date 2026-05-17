import { useRef, useState, useEffect, useCallback } from 'react'
import { Stage, Layer, Image as KonvaImage, Rect, Text, Transformer, Group } from 'react-konva'
import useImage from 'use-image'
import Konva from 'konva'
import type { LayoutRegion } from '../types'

interface DLACanvasProps {
  imageUrl: string
  regions: LayoutRegion[]
  selectedRegionId: number | null
  onSelectRegion: (id: number | null) => void
  onRegionMoved: (id: number, x: number, y: number, w: number, h: number) => void
  onNewRegion: (x: number, y: number, w: number, h: number) => void
  drawingMode: boolean
}

const MIN_SIZE = 12

function hexToRgba(hex: string, alpha: number) {
  const r = parseInt(hex.slice(1, 3), 16)
  const g = parseInt(hex.slice(3, 5), 16)
  const b = parseInt(hex.slice(5, 7), 16)
  return `rgba(${r},${g},${b},${alpha})`
}

export function DLACanvas({
  imageUrl, regions, selectedRegionId,
  onSelectRegion, onRegionMoved, onNewRegion, drawingMode,
}: DLACanvasProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const [containerSize, setContainerSize] = useState({ width: 800, height: 600 })
  const [image, imageStatus] = useImage(imageUrl, 'anonymous')
  const transformerRef = useRef<Konva.Transformer>(null)
  const selectedNodeRef = useRef<Konva.Rect | null>(null)

  const scale = image
    ? Math.min(containerSize.width / image.width, containerSize.height / image.height, 1)
    : 1
  const imgW = (image?.width ?? 0) * scale
  const imgH = (image?.height ?? 0) * scale
  const imgOffsetX = (containerSize.width - imgW) / 2
  const imgOffsetY = (containerSize.height - imgH) / 2

  useEffect(() => {
    if (!containerRef.current) return
    const ro = new ResizeObserver(entries => {
      const { width, height } = entries[0].contentRect
      setContainerSize({ width, height })
    })
    ro.observe(containerRef.current)
    return () => ro.disconnect()
  }, [])

  useEffect(() => {
    if (!transformerRef.current) return
    if (selectedNodeRef.current && selectedRegionId !== null) {
      transformerRef.current.nodes([selectedNodeRef.current])
    } else {
      transformerRef.current.nodes([])
    }
    transformerRef.current.getLayer()?.batchDraw()
  }, [selectedRegionId])

  // ─── Dibujo nuevo rect ────────────────────────────────────────────────────
  const drawing = useRef(false)
  const drawStart = useRef({ x: 0, y: 0 })
  const [drawRect, setDrawRect] = useState<{ x: number; y: number; w: number; h: number } | null>(null)

  const handleMouseDown = useCallback((e: Konva.KonvaEventObject<MouseEvent>) => {
    if (!drawingMode) return
    const isBackground = e.target === e.target.getStage() || e.target instanceof Konva.Image
    if (!isBackground) return
    const pos = e.target.getStage()!.getPointerPosition()!
    drawing.current = true
    drawStart.current = pos
    setDrawRect({ x: pos.x, y: pos.y, w: 0, h: 0 })
    onSelectRegion(null)
  }, [drawingMode, onSelectRegion])

  const handleMouseMove = useCallback((e: Konva.KonvaEventObject<MouseEvent>) => {
    if (!drawing.current) return
    const pos = e.target.getStage()!.getPointerPosition()!
    setDrawRect({
      x: Math.min(pos.x, drawStart.current.x),
      y: Math.min(pos.y, drawStart.current.y),
      w: Math.abs(pos.x - drawStart.current.x),
      h: Math.abs(pos.y - drawStart.current.y),
    })
  }, [])

  const handleMouseUp = useCallback(() => {
    if (!drawing.current || !drawRect) return
    drawing.current = false
    if (drawRect.w > MIN_SIZE && drawRect.h > MIN_SIZE) {
      onNewRegion(
        (drawRect.x - imgOffsetX) / scale,
        (drawRect.y - imgOffsetY) / scale,
        drawRect.w / scale,
        drawRect.h / scale,
      )
    }
    setDrawRect(null)
  }, [drawRect, scale, imgOffsetX, imgOffsetY, onNewRegion])

  return (
    <div
      ref={containerRef}
      className="flex-1 bg-slate-200 overflow-hidden"
      style={{ cursor: drawingMode ? 'crosshair' : 'default' }}
    >
      {imageStatus === 'loading' && (
        <div className="flex items-center justify-center h-full text-slate-400">Cargando imagen…</div>
      )}
      <Stage
        width={containerSize.width}
        height={containerSize.height}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onClick={e => { if (!drawingMode && e.target === e.target.getStage()) onSelectRegion(null) }}
      >
        <Layer>
          {/* Imagen */}
          {image && (
            <KonvaImage
              image={image}
              x={imgOffsetX} y={imgOffsetY}
              width={imgW} height={imgH}
            />
          )}

          {/* Regiones anotadas */}
          {regions.map(region => {
            const isSelected = region.id === selectedRegionId
            const color = region.type_color ?? '#6366f1'
            const x = imgOffsetX + region.bbox_x * scale
            const y = imgOffsetY + region.bbox_y * scale
            const w = region.bbox_width * scale
            const h = region.bbox_height * scale

            return (
              <Group key={region.id}>
                <Rect
                  ref={isSelected ? (node) => { selectedNodeRef.current = node } : undefined}
                  x={x} y={y} width={w} height={h}
                  stroke={color}
                  strokeWidth={isSelected ? 2.5 : 1.8}
                  fill={hexToRgba(color, isSelected ? 0.18 : 0.08)}
                  cornerRadius={3}
                  draggable={!drawingMode}
                  onClick={() => !drawingMode && onSelectRegion(region.id)}
                  onDragEnd={e => {
                    const node = e.target
                    onRegionMoved(
                      region.id,
                      (node.x() - imgOffsetX) / scale,
                      (node.y() - imgOffsetY) / scale,
                      node.width() / scale,
                      node.height() / scale,
                    )
                  }}
                  onTransformEnd={e => {
                    const node = e.target as Konva.Rect
                    const sx = node.scaleX(), sy = node.scaleY()
                    node.scaleX(1); node.scaleY(1)
                    onRegionMoved(
                      region.id,
                      (node.x() - imgOffsetX) / scale,
                      (node.y() - imgOffsetY) / scale,
                      Math.max(10, node.width() * sx) / scale,
                      Math.max(10, node.height() * sy) / scale,
                    )
                  }}
                />
                {/* Etiqueta del tipo de región */}
                {region.type_name && (
                  <Text
                    x={x + 4} y={y + 4}
                    text={region.type_name}
                    fontSize={11}
                    fontStyle="bold"
                    fill={color}
                    listening={false}
                  />
                )}
              </Group>
            )
          })}

          {/* Rect en proceso de dibujo */}
          {drawRect && drawRect.w > 0 && (
            <Rect
              x={drawRect.x} y={drawRect.y}
              width={drawRect.w} height={drawRect.h}
              stroke="#6366f1"
              strokeWidth={1.5}
              fill="rgba(99,102,241,0.1)"
              dash={[5, 3]}
              listening={false}
            />
          )}

          <Transformer
            ref={transformerRef}
            rotateEnabled={false}
            boundBoxFunc={(_, nb) => ({
              ...nb,
              width: Math.max(10, nb.width),
              height: Math.max(10, nb.height),
            })}
          />
        </Layer>
      </Stage>
    </div>
  )
}

