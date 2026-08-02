import type {
  Project, ProjectCreate,
  Document, DocumentStatus,
  Word, WordCreate, WordUpdate,
  LabelSchema, LabelSchemaCreate,
  SegmentationResult, SegmentationMethod,
  LayoutRegionType, LayoutRegionTypeCreate,
  LayoutRegion, LayoutRegionCreate, LayoutRegionUpdate, LayoutRegionSegmentationResult,
} from '../types'

const BASE = 'http://localhost:8000/api/v1'

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail ?? 'Error en la API')
  }
  return res.json() as Promise<T>
}

// ─── Proyectos ────────────────────────────────────────────────────────────────
export const api = {
  projects: {
    list: () => request<Project[]>('/projects/'),
    get: (id: number) => request<Project>(`/projects/${id}`),
    create: (data: ProjectCreate) =>
      request<Project>('/projects/', { method: 'POST', body: JSON.stringify(data) }),
    update: (id: number, data: Partial<ProjectCreate>) =>
      request<Project>(`/projects/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
    delete: (id: number) =>
      fetch(`${BASE}/projects/${id}`, { method: 'DELETE' }),
  },

  // ─── Documentos ─────────────────────────────────────────────────────────────
  documents: {
    list: (projectId: number) =>
      request<Document[]>(`/projects/${projectId}/documents/`),
    get: (projectId: number, docId: number) =>
      request<Document>(`/projects/${projectId}/documents/${docId}`),
    upload: (projectId: number, file: File) => {
      const form = new FormData()
      form.append('file', file)
      return fetch(`${BASE}/projects/${projectId}/documents/`, {
        method: 'POST',
        body: form,
      }).then(r => {
        if (!r.ok) throw new Error('Error al subir el archivo')
        return r.json() as Promise<Document>
      })
    },
    imageUrl: (projectId: number, docId: number) =>
      `${BASE}/projects/${projectId}/documents/${docId}/image`,
    updateStatus: (projectId: number, docId: number, status: DocumentStatus) =>
      request<Document>(`/projects/${projectId}/documents/${docId}/status`, {
        method: 'PATCH',
        body: JSON.stringify({ status }),
      }),
    delete: (projectId: number, docId: number) =>
      fetch(`${BASE}/projects/${projectId}/documents/${docId}`, { method: 'DELETE' }),
  },

  // ─── Palabras ───────────────────────────────────────────────────────────────
  words: {
    list: (docId: number) => request<Word[]>(`/documents/${docId}/words/`),
    create: (docId: number, data: WordCreate) =>
      request<Word>(`/documents/${docId}/words/`, { method: 'POST', body: JSON.stringify(data) }),
    bulkCreate: (docId: number, words: WordCreate[]) =>
      request<Word[]>(`/documents/${docId}/words/bulk`, {
        method: 'POST',
        body: JSON.stringify({ words }),
      }),
    update: (docId: number, wordId: number, data: WordUpdate) =>
      request<Word>(`/documents/${docId}/words/${wordId}`, {
        method: 'PATCH',
        body: JSON.stringify(data),
      }),
    delete: (docId: number, wordId: number) =>
      fetch(`${BASE}/documents/${docId}/words/${wordId}`, { method: 'DELETE' }),
    assignLabel: (docId: number, wordId: number, labelSchemaId: number) =>
      request(`/documents/${docId}/words/${wordId}/labels`, {
        method: 'POST',
        body: JSON.stringify({ label_schema_id: labelSchemaId }),
      }),
    removeLabel: (docId: number, wordId: number, labelSchemaId: number) =>
      fetch(`${BASE}/documents/${docId}/words/${wordId}/labels/${labelSchemaId}`, {
        method: 'DELETE',
      }),
  },

  // ─── Esquemas de etiquetas ──────────────────────────────────────────────────
  labels: {
    list: (projectId: number) =>
      request<LabelSchema[]>(`/projects/${projectId}/labels/`),
    create: (projectId: number, data: LabelSchemaCreate) =>
      request<LabelSchema>(`/projects/${projectId}/labels/`, {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    update: (projectId: number, labelId: number, data: Partial<LabelSchemaCreate>) =>
      request<LabelSchema>(`/projects/${projectId}/labels/${labelId}`, {
        method: 'PATCH',
        body: JSON.stringify(data),
      }),
    delete: (projectId: number, labelId: number) =>
      fetch(`${BASE}/projects/${projectId}/labels/${labelId}`, { method: 'DELETE' }),
  },

  // ─── Segmentación asistida ──────────────────────────────────────────────────
  segmentation: {
    preview: (docId: number, method: SegmentationMethod = 'contour') =>
      request<SegmentationResult>(`/documents/${docId}/segment?method=${method}`, {
        method: 'POST',
      }),
    apply: (docId: number, method: SegmentationMethod = 'contour') =>
      request<Word[]>(`/documents/${docId}/segment/apply?method=${method}`, {
        method: 'POST',
      }),
  },

  // ─── DLA — Document Layout Analysis ───────────────────────────────────────
  layoutTypes: {
    list: (projectId: number) =>
      request<LayoutRegionType[]>(`/projects/${projectId}/layout-region-types/`),
    create: (projectId: number, data: LayoutRegionTypeCreate) =>
      request<LayoutRegionType>(`/projects/${projectId}/layout-region-types/`, {
        method: 'POST', body: JSON.stringify(data),
      }),
    seedDefaults: (projectId: number) =>
      request<LayoutRegionType[]>(`/projects/${projectId}/layout-region-types/seed-defaults`, {
        method: 'POST',
      }),
    update: (projectId: number, typeId: number, data: Partial<LayoutRegionTypeCreate>) =>
      request<LayoutRegionType>(`/projects/${projectId}/layout-region-types/${typeId}`, {
        method: 'PATCH', body: JSON.stringify(data),
      }),
    delete: (projectId: number, typeId: number) =>
      fetch(`${BASE}/projects/${projectId}/layout-region-types/${typeId}`, { method: 'DELETE' }),
  },

  layoutRegions: {
    list: (docId: number) =>
      request<LayoutRegion[]>(`/documents/${docId}/layout-regions/`),
    create: (docId: number, data: LayoutRegionCreate) =>
      request<LayoutRegion>(`/documents/${docId}/layout-regions/`, {
        method: 'POST', body: JSON.stringify(data),
      }),
    update: (docId: number, regionId: number, data: LayoutRegionUpdate) =>
      request<LayoutRegion>(`/documents/${docId}/layout-regions/${regionId}`, {
        method: 'PATCH', body: JSON.stringify(data),
      }),
    delete: (docId: number, regionId: number) =>
      fetch(`${BASE}/documents/${docId}/layout-regions/${regionId}`, { method: 'DELETE' }),
    segmentPreview: (docId: number) =>
      request<LayoutRegionSegmentationResult>(`/documents/${docId}/layout-regions/segment`, {
        method: 'POST',
      }),
    segmentApply: (docId: number) =>
      request<LayoutRegion[]>(`/documents/${docId}/layout-regions/segment/apply`, {
        method: 'POST',
      }),
  },
}
