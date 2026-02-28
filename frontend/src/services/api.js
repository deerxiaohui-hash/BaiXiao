import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json'
  }
})

export const uploadDocument = async (file, onProgress) => {
  const formData = new FormData()
  formData.append('file', file)
  
  return api.post('/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    },
    onUploadProgress: (progressEvent) => {
      if (onProgress) {
        const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total)
        onProgress(percentCompleted)
      }
    }
  })
}

export const sendMessage = async (question) => {
  return api.post('/chat', { question })
}

export const getDocuments = async () => {
  return api.get('/documents')
}

export const deleteDocument = async (documentId) => {
  return api.delete(`/documents/${documentId}`)
}

export default api
