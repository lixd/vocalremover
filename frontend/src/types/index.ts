export interface Task {
  id: string
  status: 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED'
  mode: '2stems' | '4stems'
  original_filename: string
  file_size: number
  created_at: string
  updated_at: string
  completed_at: string | null
  error_message: string | null
  stems: Record<string, StemInfo>
}

export type TaskStatus = Task['status']
export type SeparationMode = Task['mode']

export interface StemInfo {
  filename: string
  size: number
  duration?: number
}
