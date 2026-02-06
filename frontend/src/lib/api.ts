import axios from "axios";
 
// Your correct port
const API_BASE_URL = "http://localhost:8001/api/v1";
 
// Axios instance with default config
export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});
 
// ---- JWT AUTHENTICATION ---- //
 
// Attach token to every request (if present) via interceptor
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
 
// ---- AUTH ENDPOINTS ---- //
 
export const registerUser = async (data) => {
  const response = await api.post("/auth/register", data);
  return response.data;
};
 
export const loginUser = async (data) => {
  const response = await api.post("/auth/login", data);
  return response.data;
};
 
export const deleteFile = async (jobId: string) => {
  const response = await api.delete(`/files/${jobId}`);
  return response.data;
};
// ---- WORKFLOW/FILE UPLOAD ---- //
 
export const uploadStudentPaper = async (formData: FormData) => {
  const response = await api.post("/workflow/autonomous", formData, {
    headers: { "Content-Type": "multipart/form-data" }, // Authorization auto-attached!
  });
  return response.data.data;
};
 
export const uploadReference = async (formData: FormData) => {
  const response = await api.post("/reference/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return response.data.data;
};
 
export const getSavedFiles = async () => {
  const response = await api.get("/files/");
  return response.data;
};
 
export const reprocessFile = async (jobId: string) => {
  const response = await api.post(`/files/reprocess/${jobId}`);
  return response.data;
};
 
export const getHistory = async (params?: { status?: string; limit?: number }) => {
  const response = await api.get("/history/", { params });
  return response.data;
};
 
// ---- REFERENCES, LISTS ---- //
 
export const getReferenceList = async (params) => {
  const response = await api.get("/reference/list", { params });
  return response.data;
};
 
export const getReferenceById = async (referenceId) => {
  const response = await api.get(`/reference/${referenceId}`);
  return response.data;
};
 
// ---- JOB STATUS, REPORTS ---- //
 
export const getJobStatus = async (jobId) => {
  const response = await api.get(`/upload/${jobId}/status`);
  return response.data;
};
 
export const downloadReport = async (jobId) => {
  const response = await api.get(`/report/download/${jobId}`, {
    responseType: "blob",
  });
  return response.data;
};
 
// ---- REVIEW, ASSESSMENTS ---- //
 
export const updateReview = async (data) => {
  const response = await api.put("/review/", data);
  return response.data;
};
 
export const reassessAnswers = async (data: {
  job_id: string;
  reference_id: string | null  
}) => {
  const response = await api.post('/reassess/', data);
  return response.data;
};
 
 
// ---- FEEDBACK, REPORT GENERATION ---- //
 
export const generateReport = async (data) => {
  const payload = { ...data, format: data.format || 'pdf' };
  const response = await api.post("/report/generate", payload);
  return response.data;
};
 
export const generateFeedback = async (data) => {
  const response = await api.post("/feedback/", data);
  return response.data;
};
 
// ---- HEALTH CHECK ---- //
 
export const checkHealth = async () => {
  const response = await api.get("/health/");
  return response.data;
};

// ---- TEACHER DASHBOARD ENDPOINTS ---- //

export const getTeacherReferences = async () => {
  const response = await api.get("/teacher/my-references");
  return response.data;
};

export const getSubmissionsForReference = async (referenceId: string) => {
  const response = await api.get(`/teacher/submissions/${referenceId}`);
  return response.data;
};

export const getStudentReport = async (jobId: string) => {
  const response = await api.get(`/teacher/student-report/${jobId}`);
  return response.data;
};

export const getClassStatistics = async (referenceId: string) => {
  const response = await api.get(`/teacher/class-statistics/${referenceId}`);
  return response.data;
};

// ---- USER PROFILE ---- //

export const getCurrentUser = () => {
  const userStr = localStorage.getItem("current_user");
  return userStr ? JSON.parse(userStr) : null;
};

export const getUserRole = () => {
  const user = getCurrentUser();
  return user?.role || null;
};
