import api from "./api";

export const getReviewQueue = (page = 1, perPage = 20, queueType = "all") =>
  api.get("/admin/review-queue", { params: { page, per_page: perPage, queue_type: queueType } });

export const overrideClassification = (requestId, classification, reasoning) =>
  api.post(`/admin/requests/${requestId}/override-classification`, { classification, reasoning });

export const overrideRouting = (requestId, destination, reasoning) =>
  api.post(`/admin/requests/${requestId}/override-routing`, { destination, reasoning });

export const updateRequestStatus = (requestId, status, notes) =>
  api.post(`/admin/requests/${requestId}/status`, { status, notes });

export const addAdminComment = (requestId, comment) =>
  api.post(`/admin/requests/${requestId}/comment`, { comment });

export const getRequestAudit = (requestId) =>
  api.get(`/admin/requests/${requestId}/audit`);
