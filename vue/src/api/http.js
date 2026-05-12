import axios from 'axios';

const baseURL = process.env.VUE_APP_API_BASE_URL || 'http://127.0.0.1:18808';

export const api = axios.create({
  baseURL,
});

