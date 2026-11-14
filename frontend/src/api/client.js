import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

const client = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request Interceptor: Attach JWT Bearer Token
client.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('adaptive_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response Interceptor: Handle Session Expiration / 401 Unauthorized
client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      // Clear session
      localStorage.removeItem('adaptive_token');
      localStorage.removeItem('adaptive_user');
      localStorage.removeItem('adaptive_role');
      
      // If not already on login page, redirect
      const path = window.location.pathname;
      if (path !== '/' && !path.includes('/login')) {
        window.location.href = '/';
      }
    }
    return Promise.reject(error);
  }
);

export default client;

