// ─── Proyectos ────────────────────────────────────────────────────────────────
export interface Project {
  id: number
  name: string
  description: string | null
  created_at: string
  updated_at: string
  document_count: number
}

export interface ProjectCreate {
  name: string
  description?: string
}

// ─── Documentos ───────────────────────────────────────────────────────────────
export type DocumentStatus = 'pending' | 'in_progress' | 'completed'

export interface Document {
  id: number
  project_id: number
  filename: string
  original_filename: string
  image_width: number | null
  image_height: number | null
  status: DocumentStatus
  word_count: number
  labeled_count: number
  created_at: string
  updated_at: string
}

// ─── Palabras ─────────────────────────────────────────────────────────────────
export interface WordLabel {
  id: number
  label_schema_id: number
  label_name: string | null
  label_color: string | null
}

export interface Word {
  id: number
  document_id: number
  order_index: number
  bbox_x: number | null
  bbox_y: number | null
  bbox_width: number | null
  bbox_height: number | null
  transcription: string | null
  confidence: number | null
  source: 'manual' | 'auto'
  notes: string | null
  created_at: string
  updated_at: string
  labels: WordLabel[]
}

export interface WordCreate {
  order_index: number
  bbox_x?: number
  bbox_y?: number
  bbox_width?: number
  bbox_height?: number
  transcription?: string
  source?: 'manual' | 'auto'
  confidence?: number
}

export interface WordUpdate {
  transcription?: string
  notes?: string
  bbox_x?: number
  bbox_y?: number
  bbox_width?: number
  bbox_height?: number
  order_index?: number
}

// ─── Esquemas de etiquetas ────────────────────────────────────────────────────
export interface LabelSchema {
  id: number
  project_id: number
  name: string
  color: string
  description: string | null
  shortcut: string | null
  created_at: string
}

export interface LabelSchemaCreate {
  name: string
  color?: string
  description?: string
  shortcut?: string
}

// ─── Segmentación asistida ────────────────────────────────────────────────────
export interface BBox {
  x: number
  y: number
  width: number
  height: number
}

export interface SegmentedWord {
  bbox: BBox
  confidence: number
  order_index: number
}

export type SegmentationMethod = 'contour' | 'projection' | 'mser'

// ─── DLA — Document Layout Analysis ─────────────────────────────────────────
export interface LayoutRegionType {
  id: number
  project_id: number
  name: string
  color: string
  description: string | null
  shortcut: string | null
  created_at: string
}

export interface LayoutRegionTypeCreate {
  name: string
  color?: string
  description?: string
  shortcut?: string
}

export interface LayoutRegion {
  id: number
  document_id: number
  region_type_id: number | null
  order_index: number
  bbox_x: number
  bbox_y: number
  bbox_width: number
  bbox_height: number
  notes: string | null
  created_at: string
  updated_at: string
  type_name: string | null
  type_color: string | null
}

export interface LayoutRegionCreate {
  bbox_x: number
  bbox_y: number
  bbox_width: number
  bbox_height: number
  region_type_id?: number | null
  order_index?: number
  notes?: string
}

export interface LayoutRegionUpdate {
  bbox_x?: number
  bbox_y?: number
  bbox_width?: number
  bbox_height?: number
  region_type_id?: number | null
  order_index?: number
  notes?: string
  source: 'manual' | 'auto'
}

export interface SegmentedLayoutRegion {
  bbox: BBox
  region_type_name: string
  confidence: number
  order_index: number
}

export interface LayoutRegionSegmentationResult {
  document_id: number
  total_regions: number
  regions: SegmentedLayoutRegion[]
}
