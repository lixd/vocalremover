import axios from 'axios'
import type { Task } from '@/types'

export async function createTask(formData: FormData): Promise<Task> {
  const response = await axios.post<Task>('/api/tasks/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return response.data
}

export async function getTaskStatus(taskId: string): Promise<Task> {
  const response = await axios.get<Task>(`/api/tasks/${taskId}/`)
  return response.data
}

export async function getStems(
  taskId: string
): Promise<Record<string, { filename: string; size?: number }>> {
  const response = await axios.get(`/api/tasks/${taskId}/stems/`)
  return response.data
}

export function getStemStreamUrl(taskId: string, stemName: string): string {
  return `/api/tasks/${taskId}/stems/${stemName}/stream/`
}

export function getStemDownloadUrl(taskId: string, stemName: string): string {
  return `/api/tasks/${taskId}/stems/${stemName}/`
}

export function getDownloadAllUrl(taskId: string): string {
  return `/api/tasks/${taskId}/stems/download-all/`
}
