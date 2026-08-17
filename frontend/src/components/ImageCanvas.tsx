import { useRef, useState, useEffect, useCallback } from 'react'
import { Stage, Layer, Image as KonvaImage, Rect, Transformer, Text } from 'react-konva'
import useImage from 'use-image'
import Konva from 'konva'
import type { Word, LabelSchema, SegmentedWord } from '../../types'
import { useZoomPan } from '../hooks/useZoomPan'
import { ZoomControls } from './ZoomControls'

interface ImageCanvasProps {
  imageUrl: string
  words: Word[]
  previewWords?: SegmentedWord[]   // sugerencias sin guardar
  labels: LabelSchema[]
  selectedWordId: number | null
  onSelectWord: (id: number | null) => void
  onWordMoved: (wordId: number, x: number, y: number, w: number, h: number) => void
  onNewWord: (x: number, y: number, w: number, h: number) => void
  drawingMode: boolean
}

const MIN_SIZE = 8

function wordColor(word: Word, labels: LabelSchema[]): string {
  if (!word.labels.length) return '#3b82f6'
  const schema = labels.find(l => l.id === word.labels[0].label_schema_id)
  return schema?.color ?? '#3b82f6'
}

export function ImageCanvas({
  imageUrl, words, previewWords = [], labels,
  selectedWordId, onSelectWord, onWordMoved, onNewWord, drawingMode,
}: ImageCanvasProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const [containerSize, setContainerSize] = useState({ width: 800, height: 600 })
  const [image, imageStatus] = useImage(imageUrl, 'anonymous')
  const transformerRef = useRef<Konva.Transformer>(null)
  const selectedRef = useRef<Konva.Rect | null>(null)
  const { stageScale, stagePos, setStagePos, handleWheel, zoomIn, zoomOut, resetZoom } = useZoomPan()

  useEffect(() => {
    resetZoom()
  }, [imageUrl, resetZoom])

  // Escala para ajustar imagen al contenedor
  const scale = image
    ? Math.min(containerSize.width / image.width, containerSize.height / image.height, 1)
    : 1

  const imgW = (image?.width ?? 0) * scale
  const imgH = (image?.height ?? 0) * scale

  // Observar tamaño del contenedor
  useEffect(() => {
    if (!containerRef.current) return
    const ro = new ResizeObserver(entries => {
      const { width, height } = entries[0].contentRect
      setContainerSize({ width, height })
    })
    ro.observe(containerRef.current)
    return () => ro.disconnect()
  }, [])

  // Conectar transformer al rect seleccionado
  useEffect(() => {
    if (!transformerRef.current) return
    if (selectedRef.current && selectedWordId !== null) {
      transformerRef.current.nodes([selectedRef.current])
    } else {
      transformerRef.current.nodes([])
    }
    transformerRef.current.getLayer()?.batchDraw()
  }, [selectedWordId])

  // ─── Dibujo de nuevo bbox ──────────────────────────────────────────────────
  const drawing = useRef(false)
  const drawStart = useRef({ x: 0, y: 0 })
  const [drawRect, setDrawRect] = useState<{ x: number; y: number; w: number; h: number } | null>(null)

  const handleStageMouseDown = useCallback((e: Konva.KonvaEventObject<MouseEvent>) => {
    if (!drawingMode) return
    if (e.target !== e.target.getStage() && !(e.target instanceof Konva.Image)) return
    const stage = e.target.getStage()!
    const pos = stage.getRelativePointerPosition()!
    drawing.current = true
    drawStart.current = pos
    setDrawRect({ x: pos.x, y: pos.y, w: 0, h: 0 })
    onSelectWord(null)
  }, [drawingMode, onSelectWord])

  const handleStageMouseMove = useCallback((e: Konva.KonvaEventObject<MouseEvent>) => {
    if (!drawing.current) return
    const pos = e.target.getStage()!.getRelativePointerPosition()!
    setDrawRect({
      x: Math.min(pos.x, drawStart.current.x),
      y: Math.min(pos.y, drawStart.current.y),
      w: Math.abs(pos.x - drawStart.current.x),
      h: Math.abs(pos.y - drawStart.current.y),
    })
  }, [])

  const handleStageMouseUp = useCallback(() => {
    if (!drawing.current || !drawRect) return
    drawing.current = false
    if (drawRect.w > MIN_SIZE && drawRect.h > MIN_SIZE) {
      // Convertir de coordenadas canvas a coordenadas imagen original
      const imgOffsetX = (containerSize.width - imgW) / 2
      const imgOffsetY = (containerSize.height - imgH) / 2
      onNewWord(
        (drawRect.x - imgOffsetX) / scale,
        (drawRect.y - imgOffsetY) / scale,
        drawRect.w / scale,
        drawRect.h / scale,
      )
    }
    setDrawRect(null)
  }, [drawRect, scale, imgW, imgH, containerSize, onNewWord])

  const imgOffsetX = (containerSize.width - imgW) / 2
  const imgOffsetY = (containerSize.height - imgH) / 2

  return (
    <div ref={containerRef} className="relative flex-1 bg-slate-100 overflow-hidden" style={{ cursor: drawingMode ? 'crosshair' : 'default' }}>
      {imageStatus === 'loading' && (
        <div className="flex items-center justify-center h-full text-slate-400">Cargando imagen…</div>
      )}
      {imageStatus === 'failed' && (
        <div className="flex items-center justify-center h-full text-red-400">No se pudo cargar la imagen</div>
      )}
      <Stage
        width={containerSize.width}
        height={containerSize.height}
        scaleX={stageScale}
        scaleY={stageScale}
        x={stagePos.x}
        y={stagePos.y}
        draggable={!drawingMode}
        onWheel={handleWheel}
        onDragEnd={(e) => {
          if (e.target === e.target.getStage()) {
            setStagePos({ x: e.target.x(), y: e.target.y() })
          }
        }}
        onMouseDown={handleStageMouseDown}
        onMouseMove={handleStageMouseMove}
        onMouseUp={handleStageMouseUp}
        onClick={(e) => {
          if (!drawingMode && e.target === e.target.getStage()) onSelectWord(null)
        }}
      >
        <Layer>
          {/* Imagen */}
          {image && (
            <KonvaImage
              image={image}
              x={imgOffsetX}
              y={imgOffsetY}
              width={imgW}
              height={imgH}
            />
          )}

          {/* Bounding boxes de palabras guardadas */}
          {words.map(word => {
            if (word.bbox_x == null) return null
            const isSelected = word.id === selectedWordId
            const color = wordColor(word, labels)
            const x = imgOffsetX + word.bbox_x * scale
            const y = imgOffsetY + word.bbox_y! * scale
            const w = word.bbox_width! * scale
            const h = word.bbox_height! * scale

            return (
              <Rect
                key={word.id}
                ref={isSelected ? (node) => { selectedRef.current = node } : undefined}
                x={x} y={y} width={w} height={h}
                stroke={color}
                strokeWidth={(isSelected ? 2.5 : 1.5) / stageScale}
                fill={isSelected ? `${color}22` : `${color}11`}
                cornerRadius={2}
                draggable={!drawingMode}
                onClick={() => !drawingMode && onSelectWord(word.id)}
                onDragEnd={(e) => {
                  const node = e.target
                  onWordMoved(
                    word.id,
                    (node.x() - imgOffsetX) / scale,
                    (node.y() - imgOffsetY) / scale,
                    node.width() / scale,
                    node.height() / scale,
                  )
                }}
                onTransformEnd={(e) => {
                  const node = e.target as Konva.Rect
                  const scaleX = node.scaleX()
                  const scaleY = node.scaleY()
                  node.scaleX(1)
                  node.scaleY(1)
                  onWordMoved(
                    word.id,
                    (node.x() - imgOffsetX) / scale,
                    (node.y() - imgOffsetY) / scale,
                    Math.max(10, node.width() * scaleX) / scale,
                    Math.max(10, node.height() * scaleY) / scale,
                  )
                }}
              />
            )
          })}

          {/* Bounding boxes de previsualización (segmentación asistida) */}
          {previewWords.map((pw, i) => (
            <Rect
              key={`preview-${i}`}
              x={imgOffsetX + pw.bbox.x * scale}
              y={imgOffsetY + pw.bbox.y * scale}
              width={pw.bbox.width * scale}
              height={pw.bbox.height * scale}
              stroke="#f59e0b"
              strokeWidth={1.5 / stageScale}
              fill="#f59e0b18"
              dash={[4, 3]}
              cornerRadius={2}
              listening={false}
            />
          ))}

          {/* Rect en proceso de dibujo */}
          {drawRect && drawRect.w > 0 && (
            <Rect
              x={drawRect.x} y={drawRect.y}
              width={drawRect.w} height={drawRect.h}
              stroke="#3b82f6"
              strokeWidth={1.5 / stageScale}
              fill="#3b82f620"
              dash={[4, 3]}
              listening={false}
            />
          )}

          {/* Transformer para redimensionar */}
          <Transformer
            ref={transformerRef}
            rotateEnabled={false}
            boundBoxFunc={(_, newBox) => ({
              ...newBox,
              width: Math.max(10, newBox.width),
              height: Math.max(10, newBox.height),
            })}
          />
        </Layer>
      </Stage>
      {image && (
        <ZoomControls
          zoomPercent={Math.round(stageScale * 100)}
          onZoomIn={() => zoomIn({ x: containerSize.width / 2, y: containerSize.height / 2 })}
          onZoomOut={() => zoomOut({ x: containerSize.width / 2, y: containerSize.height / 2 })}
          onReset={resetZoom}
        />
      )}
    </div>
  )
}
