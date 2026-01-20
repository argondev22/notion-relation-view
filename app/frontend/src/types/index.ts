// Type definitions

export interface Node {
  id: string
  title: string
  databaseId: string
  x: number
  y: number
  visible: boolean
}

export interface Edge {
  id: string
  sourceId: string
  targetId: string
  relationProperty: string
  visible: boolean
}

export interface Database {
  id: string
  title: string
  hidden: boolean
}

export interface ViewSettings {
  zoomLevel: number
  panX: number
  panY: number
}

export interface View {
  id: string
  name: string
  databaseIds: string[]
  settings: ViewSettings
  url: string
}

export interface GraphData {
  nodes: Node[]
  edges: Edge[]
  databases: Database[]
}

export interface User {
  id: string
  email: string
}

export interface AuthResponse {
  success: boolean
  user?: User
  error?: string
}
