import api from "./client";

export const registerUser = (data) =>
  api.post("/auth/register", data);

export const login = async (email, password) => {
  const form = new URLSearchParams();
  form.append("username", email);
  form.append("password", password);
  const res = await api.post("/auth/token", form, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });
  return res.data;
};

export const predict7Class = (file) => {
  const form = new FormData();
  form.append("file", file);
  return api.post("/predict/7class", form);
};

export const predictBinary = (file) => {
  const form = new FormData();
  form.append("file", file);
  return api.post("/predict/binary", form);
};

export const explain7Class = (file) => {
  const form = new FormData();
  form.append("file", file);
  return api.post("/predict/7class/explain", form);
};

export const submitFeedback = (data) =>
  api.post("/feedback/", data);

export const submitNewCase = (formData) =>
  api.post("/new_case/submit", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });

export const listPendingCases = () => api.get("/admin/pending_cases");
export const approveCase = (id) => api.post(`/admin/approve_case/${id}`);
export const getRetrainingQueue = () => api.get("/admin/retraining_queue");
export const triggerRetrain = () => api.post("/admin/trigger_retrain");