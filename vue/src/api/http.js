import axios from 'axios';
import { getAuthToken } from '@/auth/storage';

const baseURL = process.env.VUE_APP_API_BASE_URL || 'http://127.0.0.1:18808';

export const api = axios.create({
  baseURL,
});

api.interceptors.request.use((config) => {
  const token = getAuthToken();
  if (token) {
    config.headers = config.headers || {};
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
