import { useState, useCallback } from 'react'
import type Konva from 'konva'

const MIN_ZOOM = 1
const MAX_ZOOM = 8
const WHEEL_ZOOM_STEP = 1.05
const BUTTON_ZOOM_STEP = 1.3

export function useZoomPan() {
    const [stageScale, setStageScale] = useState(1)
    const [stagePos, setStagePos] = useState({ x: 0, y: 0 })

    const zoomAt = useCallback((point: { x: number; y: number }, factor: number) => {
        const newScale = Math.min(MAX_ZOOM, Math.max(MIN_ZOOM, stageScale * factor))

        const imagePoint = {
            x: (point.x - stagePos.x) / stageScale,
            y: (point.y - stagePos.y) / stageScale,
        }

        setStagePos({
            x: point.x - imagePoint.x * newScale,
            y: point.y - imagePoint.y * newScale,
        })
        setStageScale(newScale)
    }, [stageScale, stagePos])

    const handleWheel = useCallback((e: Konva.KonvaEventObject<WheelEvent>) => {
        e.evt.preventDefault()
        const stage = e.target.getStage()
        if (!stage) return
        const pointer = stage.getPointerPosition()
        if (!pointer) return
        const factor = e.evt.deltaY > 0 ? 1 / WHEEL_ZOOM_STEP : WHEEL_ZOOM_STEP
        zoomAt(pointer, factor)
    }, [zoomAt])

    const zoomIn = useCallback((center: { x: number; y: number }) => {
        zoomAt(center, BUTTON_ZOOM_STEP)
    }, [zoomAt])

    const zoomOut = useCallback((center: { x: number; y: number }) => {
        zoomAt(center, 1 / BUTTON_ZOOM_STEP)
    }, [zoomAt])

    const resetZoom = useCallback(() => {
        setStageScale(1)
        setStagePos({ x: 0, y: 0 })
    }, [])

    return { stageScale, stagePos, setStagePos, handleWheel, zoomIn, zoomOut, resetZoom }
}