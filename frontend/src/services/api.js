import axios from "axios";

const api = axios.create({
  baseURL: "/api",
  headers: {
    "Content-Type": "application/json",
  },
});

// Retrieve network departments
export const getDepartments = async () => {
  const response = await api.get("/departments");
  return response.data;
};

// Retrieve network policies
export const getPolicies = async () => {
  const response = await api.get("/policies");
  return response.data;
};

// Apply natural-language intent
export const applyIntent = async (intent) => {
  const response = await api.post("/intent/apply", {
    intent,
  });
  return response.data;
};

// Update existing policy
export const updatePolicy = async (policyName, action) => {
  const response = await api.patch(
    `/policies/${encodeURIComponent(policyName)}`,
    { action }
  );
  return response.data;
};

// Retrieve network monitoring information
export const getNetworkMetrics = async () => {
  const response = await api.get("/monitoring");
  return response.data.network;
};

// Retrieve recent activity logs
export const getActivities = async () => {
  const response = await api.get("/activity?limit=20");
  return response.data;
};

export default api;
