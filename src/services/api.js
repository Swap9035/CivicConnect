import axios from "axios";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  "https://matching-mice-flowers-operational.trycloudflare.com";

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Add token to requests if available
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// API functions
export const authAPI = {
  signup: (userData) => api.post("/users/signup", userData),
  login: (credentials) => api.post("/users/login", credentials),
  adminLogin: (credentials) =>
    api.post("/superuser/auth/auth/login", credentials),
  getCurrentUser: () => api.get("/users/me"),
  getAdminProfile: () => api.get("/superuser/auth/auth/profile"),
  changeAdminPassword: (data) =>
    api.post("/superuser/auth/auth/change-password", data),
  adminLogout: () => api.post("/superuser/auth/auth/logout"),
};

// Admin API functions
export const adminAPI = {
  // Create a new staff user
  createUser: (userData) =>
    api.post("/superuser/admin/admin/create-user", userData),

  // Get list of users with filters
  getUsers: (filters = {}) => {
    const params = new URLSearchParams();
    if (filters.dept) params.append("dept", filters.dept);
    if (filters.ward) params.append("ward", filters.ward);
    if (filters.role) params.append("role", filters.role);
    params.append("page", filters.page || 1);
    params.append("page_size", filters.page_size || 10);
    return api.get(`/superuser/admin/admin/users?${params.toString()}`);
  },

  // Get specific user details
  getUserDetails: (staffId) =>
    api.get(`/superuser/admin/admin/users/${staffId}`),

  // Update user's jurisdiction
  updateJurisdiction: (data) =>
    api.put("/superuser/admin/admin/update-jurisdiction", data),
};

// Grievance API functions
export const grievanceAPI = {
  // Start new grievance session
  start: (formData) =>
    api.post("/grievance/start", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    }),

  // Send clarification response
  clarify: (data) => api.post("/grievance/clarify", data),

  // Submit final grievance
  submit: (data) => api.post("/grievance/submit", data),

  // Get grievance form details
  getForm: (formId) => api.get(`/grievance/form/${formId}`),

  // Get session details
  getSession: (sessionId) => api.get(`/grievance/session/${sessionId}`),

  // Confirm resolution
  confirmResolution: (formId) =>
    api.post(`/grievance/forms/${formId}/confirm-resolution`),

  // Get grievance status
  getStatus: (formId) => api.get(`/grievance/status/${formId}`),

  // Get all grievance forms
  getForms: () => api.get(`/grievance/forms`),
};

// Officer Resolution API functions
export const officerAPI = {
  // Get officer's dashboard with all assigned tickets
  getDashboard: () => api.get("/resolution/officer/dashboard"),

  // Update ticket status
  updateStatus: (data) => api.patch("/resolution/officer/update-status", data),

  // Convenience helpers
  startWork: (data) => api.patch("/resolution/officer/start", data),
  pauseWork: (data) => api.patch("/resolution/officer/pause", data),
  resumeWork: (data) => api.patch("/resolution/officer/resume", data),

  // Request clarification from citizen
  requestClarification: (data) =>
    api.post("/resolution/officer/request-clarification", data),

  // Resolve ticket with proof photos
  resolveTicket: (formData) =>
    api.post("/resolution/officer/resolve", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    }),

  // Get specific ticket details
  getTicketDetails: (grievanceId) =>
    api.get(`/resolution/officer/ticket/${grievanceId}`),

  // Get all clarifications
  getClarifications: () => api.get("/resolution/officer/clarifications"),

  // Get resolved tickets
  getResolvedTickets: () => api.get("/resolution/officer/resolved"),

  // Get ticket counts by status
  getTicketCounts: () => api.get("/resolution/officer/total"),
};

// Feedback API functions
export const feedbackAPI = {
  getConflicts: (skip = 0, limit = 20) =>
    api.get(`/feedback/conflicts/list?skip=${skip}&limit=${limit}`),
  getFeedbacks: (skip = 0, limit = 50) =>
    api.get(`/feedback/list?skip=${skip}&limit=${limit}`),
  getFeedback: (feedbackId) => api.get(`/feedback/id/${feedbackId}`),
};

export default api;
