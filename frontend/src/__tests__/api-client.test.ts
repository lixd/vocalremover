import { describe, it, expect, vi, beforeEach } from 'vitest'
import axios from 'axios'
import { createTask, getTaskStatus, getStems } from '@/api/client'

vi.mock('axios')
const mockedAxios = vi.mocked(axios, true)

describe('API Client', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('createTask', () => {
    it('sends multipart POST with file and mode', async () => {
      const mockResponse = {
        data: {
          id: 'abc-123',
          status: 'PENDING',
          mode: '2stems',
          original_filename: 'song.mp3',
        },
      }
      mockedAxios.post.mockResolvedValue(mockResponse)

      const formData = new FormData()
      formData.append('file', new File(['audio'], 'song.mp3'))
      formData.append('mode', '2stems')

      const result = await createTask(formData)
      expect(result.id).toBe('abc-123')
      expect(result.status).toBe('PENDING')
      expect(mockedAxios.post).toHaveBeenCalledWith('/api/tasks/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
    })

    it('throws on upload failure', async () => {
      mockedAxios.post.mockRejectedValue({
        response: { data: { file: ['Unsupported format'] } },
      })

      const formData = new FormData()
      await expect(createTask(formData)).rejects.toThrow()
    })
  })

  describe('getTaskStatus', () => {
    it('fetches task by id', async () => {
      const mockResponse = {
        data: { id: 'abc-123', status: 'COMPLETED', stems: {} },
      }
      mockedAxios.get.mockResolvedValue(mockResponse)

      const result = await getTaskStatus('abc-123')
      expect(result.status).toBe('COMPLETED')
      expect(mockedAxios.get).toHaveBeenCalledWith('/api/tasks/abc-123/')
    })
  })

  describe('getStems', () => {
    it('fetches stems for completed task', async () => {
      const mockStems = {
        vocals: { filename: 'vocals.wav' },
        accompaniment: { filename: 'accompaniment.wav' },
      }
      mockedAxios.get.mockResolvedValue({ data: mockStems })

      const result = await getStems('abc-123')
      expect(result).toEqual(mockStems)
      expect(mockedAxios.get).toHaveBeenCalledWith('/api/tasks/abc-123/stems/')
    })
  })
})
