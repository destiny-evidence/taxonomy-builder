import ky from 'ky'
import { API_BASE_URL } from '../config'

export const client = ky.create({
  prefixUrl: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})
