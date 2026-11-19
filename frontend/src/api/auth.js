/**
 * BankFlow AI - Frontend API Client
 * Wraps backend authentication, customer dashboard, accounts, service requests, and profile endpoints.
 */

const API_BASE = '/api';

export const getStoredToken = () => localStorage.getItem('bankflow_token');
export const getStoredUser = () => {
  const user = localStorage.getItem('bankflow_user');
  try {
    return user ? JSON.parse(user) : null;
  } catch {
    return null;
  }
};

export const storeSession = (token, user) => {
  localStorage.setItem('bankflow_token', token);
  localStorage.setItem('bankflow_user', JSON.stringify(user));
};

export const clearSession = () => {
  localStorage.removeItem('bankflow_token');
  localStorage.removeItem('bankflow_user');
};

export const handleAuthResponse = (response) => {
  if (response.status === 401) {
    clearSession();
    if (typeof window !== 'undefined') {
      window.dispatchEvent(new CustomEvent('bankflow:auth_expired'));
    }
  }
};

const getHeaders = (includeAuth = true) => {
  const headers = { 'Content-Type': 'application/json' };
  if (includeAuth) {
    const token = getStoredToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
  }
  return headers;
};

// ============================================================================
// AUTHENTICATION ENDPOINTS
// ============================================================================

export const registerCustomer = async (data) => {
  const response = await fetch(`${API_BASE}/auth/customer/register`, {
    method: 'POST',
    headers: getHeaders(false),
    body: JSON.stringify(data),
  });
  const resData = await response.json();
  if (!response.ok) {
    throw new Error(resData.detail || 'Registration failed. Please check your inputs.');
  }
  return resData;
};

export const loginCustomer = async (data) => {
  const response = await fetch(`${API_BASE}/auth/customer/login`, {
    method: 'POST',
    headers: getHeaders(false),
    body: JSON.stringify(data),
  });
  const resData = await response.json();
  if (!response.ok) {
    throw new Error(resData.detail || 'Invalid customer credentials.');
  }
  return resData;
};

export const loginBank = async (data) => {
  const response = await fetch(`${API_BASE}/auth/bank/login`, {
    method: 'POST',
    headers: getHeaders(false),
    body: JSON.stringify(data),
  });
  const resData = await response.json();
  if (!response.ok) {
    throw new Error(resData.detail || 'Invalid employee credentials.');
  }
  return resData;
};

export const fetchMe = async () => {
  const response = await fetch(`${API_BASE}/auth/me`, {
    headers: getHeaders(true),
  });
  if (!response.ok) {
    throw new Error('Session expired or invalid.');
  }
  return await response.json();
};

export const logoutUser = async () => {
  try {
    await fetch(`${API_BASE}/auth/logout`, {
      method: 'POST',
      headers: getHeaders(true),
    });
  } finally {
    clearSession();
  }
};

// ============================================================================
// CUSTOMER DASHBOARD & ACCOUNTS ENDPOINTS
// ============================================================================

export const fetchCustomerDashboard = async () => {
  const response = await fetch(`${API_BASE}/customer/dashboard`, {
    headers: getHeaders(true),
  });
  const resData = await response.json();
  if (!response.ok) {
    throw new Error(resData.detail || 'Failed to fetch dashboard metrics.');
  }
  return resData;
};

export const fetchCustomerAccounts = async () => {
  const response = await fetch(`${API_BASE}/customer/accounts`, {
    headers: getHeaders(true),
  });
  const resData = await response.json();
  if (!response.ok) {
    throw new Error(resData.detail || 'Failed to fetch customer accounts.');
  }
  return resData;
};

export const createSyntheticAccount = async (data = { account_type: 'SAVINGS' }) => {
  const response = await fetch(`${API_BASE}/customer/accounts`, {
    method: 'POST',
    headers: getHeaders(true),
    body: JSON.stringify(data),
  });
  const resData = await response.json();
  if (!response.ok) {
    throw new Error(resData.detail || 'Failed to create synthetic account.');
  }
  return resData;
};

// ============================================================================
// SERVICE REQUESTS ENDPOINTS
// ============================================================================

export const submitServiceRequest = async (requestData) => {
  const response = await fetch(`${API_BASE}/customer/requests`, {
    method: 'POST',
    headers: getHeaders(true),
    body: JSON.stringify(requestData),
  });
  const resData = await response.json();
  if (!response.ok) {
    throw new Error(resData.detail || 'Failed to submit service request.');
  }
  return resData;
};

export const fetchServiceRequests = async ({ status = '', search = '', page = 1, limit = 20 } = {}) => {
  const params = new URLSearchParams();
  if (status && status !== 'ALL') params.append('status', status);
  if (search) params.append('search', search);
  params.append('page', page);
  params.append('limit', limit);

  const response = await fetch(`${API_BASE}/customer/requests?${params.toString()}`, {
    headers: getHeaders(true),
  });
  const resData = await response.json();
  if (!response.ok) {
    throw new Error(resData.detail || 'Failed to fetch requests list.');
  }
  return resData;
};

export const fetchServiceRequestDetail = async (requestId) => {
  const response = await fetch(`${API_BASE}/customer/requests/${requestId}`, {
    headers: getHeaders(true),
  });
  const resData = await response.json();
  if (!response.ok) {
    throw new Error(resData.detail || 'Failed to fetch request details.');
  }
  return resData;
};

export const correctServiceRequest = async (requestId, correctionData) => {
  const response = await fetch(`${API_BASE}/customer/requests/${requestId}/correction`, {
    method: 'PUT',
    headers: getHeaders(true),
    body: JSON.stringify(correctionData),
  });
  const resData = await response.json();
  if (!response.ok) {
    throw new Error(resData.detail || 'Failed to submit request correction.');
  }
  return resData;
};

// ============================================================================
// PROFILE ENDPOINTS
// ============================================================================

export const fetchCustomerProfile = async () => {
  const response = await fetch(`${API_BASE}/customer/profile`, {
    headers: getHeaders(true),
  });
  const resData = await response.json();
  if (!response.ok) {
    throw new Error(resData.detail || 'Failed to fetch customer profile.');
  }
  return resData;
};

export const updateCustomerProfile = async (profileData) => {
  const response = await fetch(`${API_BASE}/customer/profile`, {
    method: 'PUT',
    headers: getHeaders(true),
    body: JSON.stringify(profileData),
  });
  const resData = await response.json();
  if (!response.ok) {
    throw new Error(resData.detail || 'Failed to update profile.');
  }
  return resData;
};

export const fetchBankProfile = async () => {
  const response = await fetch(`${API_BASE}/bank/profile`, {
    headers: getHeaders(true),
  });
  const resData = await response.json();
  if (!response.ok) {
    throw new Error(resData.detail || 'Failed to fetch bank employee profile.');
  }
  return resData;
};

// ============================================================================
// CUSTOMER NOTIFICATIONS
// ============================================================================

export const fetchCustomerNotifications = async () => {
  const response = await fetch(`${API_BASE}/customer/notifications`, {
    headers: getHeaders(true),
  });
  const resData = await response.json();
  if (!response.ok) {
    throw new Error(resData.detail || 'Failed to fetch notifications.');
  }
  return resData;
};

export const markCustomerNotificationRead = async (notificationId) => {
  const response = await fetch(`${API_BASE}/customer/notifications/${notificationId}/read`, {
    method: 'PUT',
    headers: getHeaders(true),
  });
  const resData = await response.json();
  if (!response.ok) {
    throw new Error(resData.detail || 'Failed to mark notification as read.');
  }
  return resData;
};

// ============================================================================
// BANK EMPLOYEE DASHBOARD & REQUEST OPERATIONS (PHASE 4)
// ============================================================================

export const fetchBankDashboard = async () => {
  const response = await fetch(`${API_BASE}/bank/dashboard`, {
    headers: getHeaders(true),
  });
  const resData = await response.json();
  if (!response.ok) {
    throw new Error(resData.detail || 'Failed to fetch bank dashboard statistics.');
  }
  return resData;
};

export const fetchBankRequests = async ({
  status = '',
  service_type = '',
  priority = '',
  branch = '',
  search = '',
  page = 1,
  page_size = 10,
} = {}) => {
  const params = new URLSearchParams();
  if (status && status !== 'ALL') params.append('status', status);
  if (service_type && service_type !== 'ALL') params.append('service_type', service_type);
  if (priority && priority !== 'ALL') params.append('priority', priority);
  if (branch && branch !== 'ALL') params.append('branch', branch);
  if (search) params.append('search', search);
  params.append('page', page);
  params.append('page_size', page_size);

  const response = await fetch(`${API_BASE}/bank/requests?${params.toString()}`, {
    headers: getHeaders(true),
  });
  const resData = await response.json();
  if (!response.ok) {
    throw new Error(resData.detail || 'Failed to fetch bank requests.');
  }
  return resData;
};

export const fetchBankRequestDetails = async (requestId) => {
  const response = await fetch(`${API_BASE}/bank/requests/${requestId}`, {
    headers: getHeaders(true),
  });
  const resData = await response.json();
  if (!response.ok) {
    throw new Error(resData.detail || 'Failed to fetch request details.');
  }
  return resData;
};

export const fetchPendingRequests = async ({ search = '', page = 1, page_size = 10 } = {}) => {
  const params = new URLSearchParams();
  if (search) params.append('search', search);
  params.append('page', page);
  params.append('page_size', page_size);

  const response = await fetch(`${API_BASE}/bank/requests/pending?${params.toString()}`, {
    headers: getHeaders(true),
  });
  const resData = await response.json();
  if (!response.ok) {
    throw new Error(resData.detail || 'Failed to fetch pending requests.');
  }
  return resData;
};

export const fetchHumanReviewRequests = async ({ search = '', page = 1, page_size = 10 } = {}) => {
  const params = new URLSearchParams();
  if (search) params.append('search', search);
  params.append('page', page);
  params.append('page_size', page_size);

  const response = await fetch(`${API_BASE}/bank/requests/human-review?${params.toString()}`, {
    headers: getHeaders(true),
  });
  const resData = await response.json();
  if (!response.ok) {
    throw new Error(resData.detail || 'Failed to fetch human review requests.');
  }
  return resData;
};

export const fetchNeedsCorrectionRequests = async ({ search = '', page = 1, page_size = 10 } = {}) => {
  const params = new URLSearchParams();
  if (search) params.append('search', search);
  params.append('page', page);
  params.append('page_size', page_size);

  const response = await fetch(`${API_BASE}/bank/requests/needs-correction?${params.toString()}`, {
    headers: getHeaders(true),
  });
  const resData = await response.json();
  if (!response.ok) {
    throw new Error(resData.detail || 'Failed to fetch needs-correction requests.');
  }
  return resData;
};

export const fetchRejectedRequests = async ({ search = '', page = 1, page_size = 10 } = {}) => {
  const params = new URLSearchParams();
  if (search) params.append('search', search);
  params.append('page', page);
  params.append('page_size', page_size);

  const response = await fetch(`${API_BASE}/bank/requests/rejected?${params.toString()}`, {
    headers: getHeaders(true),
  });
  const resData = await response.json();
  if (!response.ok) {
    throw new Error(resData.detail || 'Failed to fetch rejected requests.');
  }
  return resData;
};

export const submitReviewDecision = async (requestId, reviewData) => {
  const response = await fetch(`${API_BASE}/bank/requests/${requestId}/review`, {
    method: 'POST',
    headers: getHeaders(true),
    body: JSON.stringify(reviewData),
  });
  const resData = await response.json();
  if (!response.ok) {
    throw new Error(resData.detail || 'Failed to record review decision.');
  }
  return resData;
};

export const submitCorrectionRequest = async (requestId, correctionData) => {
  const response = await fetch(`${API_BASE}/bank/requests/${requestId}/request-correction`, {
    method: 'POST',
    headers: getHeaders(true),
    body: JSON.stringify(correctionData),
  });
  const resData = await response.json();
  if (!response.ok) {
    throw new Error(resData.detail || 'Failed to request correction.');
  }
  return resData;
};

export const fetchBankCustomers = async ({ search = '', branch = '', page = 1, page_size = 10 } = {}) => {
  const params = new URLSearchParams();
  if (search) params.append('search', search);
  if (branch && branch !== 'ALL') params.append('branch', branch);
  params.append('page', page);
  params.append('page_size', page_size);

  const response = await fetch(`${API_BASE}/bank/customers?${params.toString()}`, {
    headers: getHeaders(true),
  });
  const resData = await response.json();
  if (!response.ok) {
    throw new Error(resData.detail || 'Failed to fetch customers list.');
  }
  return resData;
};

export const fetchBankCustomerDetails = async (customerId) => {
  const response = await fetch(`${API_BASE}/bank/customers/${customerId}`, {
    headers: getHeaders(true),
  });
  const resData = await response.json();
  if (!response.ok) {
    throw new Error(resData.detail || 'Failed to fetch customer profile.');
  }
  return resData;
};

export const fetchBankCustomerRequests = async (customerId) => {
  const response = await fetch(`${API_BASE}/bank/customers/${customerId}/requests`, {
    headers: getHeaders(true),
  });
  const resData = await response.json();
  if (!response.ok) {
    throw new Error(resData.detail || 'Failed to fetch customer requests.');
  }
  return resData;
};

export const fetchBankAuditLogs = async ({
  action = '',
  entity_type = '',
  entity_id = '',
  search = '',
  page = 1,
  page_size = 20,
} = {}) => {
  const params = new URLSearchParams();
  if (action && action !== 'ALL') params.append('action', action);
  if (entity_type && entity_type !== 'ALL') params.append('entity_type', entity_type);
  if (entity_id) params.append('entity_id', entity_id);
  if (search) params.append('search', search);
  params.append('page', page);
  params.append('page_size', page_size);

  const response = await fetch(`${API_BASE}/bank/audit-logs?${params.toString()}`, {
    headers: getHeaders(true),
  });
  const resData = await response.json();
  if (!response.ok) {
    throw new Error(resData.detail || 'Failed to fetch audit logs.');
  }
  return resData;
};

export const fetchRealtimeAgentMonitoring = async () => {
  const response = await fetch(`${API_BASE}/bank/agents/realtime-monitoring`, {
    headers: getHeaders(true),
  });
  const resData = await response.json();
  if (!response.ok) {
    throw new Error(resData.detail || 'Failed to fetch realtime agent monitoring data.');
  }
  return resData;
};

export const fetchBankAgents = async () => {
  const response = await fetch(`${API_BASE}/bank/agents`, {
    headers: getHeaders(true),
  });
  const resData = await response.json();
  if (!response.ok) {
    throw new Error(resData.detail || 'Failed to fetch agent monitoring status.');
  }
  return resData;
};

export const fetchAgentStatistics = async () => {
  const response = await fetch(`${API_BASE}/bank/agents/statistics`, {
    headers: getHeaders(true),
  });
  const resData = await response.json();
  if (!response.ok) {
    throw new Error(resData.detail || 'Failed to fetch agent statistics.');
  }
  return resData;
};

export const fetchSimulationStatus = async () => {
  const response = await fetch(`${API_BASE}/bank/simulation/status`, {
    headers: getHeaders(true),
  });
  const resData = await response.json();
  if (!response.ok) {
    throw new Error(resData.detail || 'Failed to fetch simulation status.');
  }
  return resData;
};

export const fetchSimulationStatistics = async () => {
  const response = await fetch(`${API_BASE}/bank/simulation/statistics`, {
    headers: getHeaders(true),
  });
  const resData = await response.json();
  if (!response.ok) {
    throw new Error(resData.detail || 'Failed to fetch simulation statistics.');
  }
  return resData;
};

export const startSimulation = async (config = {}) => {
  const response = await fetch(`${API_BASE}/bank/simulation/start`, {
    method: 'POST',
    headers: getHeaders(true),
    body: JSON.stringify(config),
  });
  const resData = await response.json();
  if (!response.ok) {
    throw new Error(resData.detail || 'Failed to start simulation.');
  }
  return resData;
};

export const stopSimulation = async () => {
  const response = await fetch(`${API_BASE}/bank/simulation/stop`, {
    method: 'POST',
    headers: getHeaders(true),
  });
  const resData = await response.json();
  if (!response.ok) {
    throw new Error(resData.detail || 'Failed to stop simulation.');
  }
  return resData;
};

export const runSimulationScenario = async (scenarioId) => {
  const response = await fetch(`${API_BASE}/bank/simulation/run-test`, {
    method: 'POST',
    headers: getHeaders(true),
    body: JSON.stringify({ scenario_id: Number(scenarioId) }),
  });
  const resData = await response.json();
  if (!response.ok) {
    throw new Error(resData.detail || 'Failed to run scenario benchmark.');
  }
  return resData;
};

// ============================================================================
// PHASE 6: MULTI-AGENT MESSAGING & RABBITMQ BROKER INSPECTION
// ============================================================================

export const fetchBrokerStatus = async () => {
  const response = await fetch(`${API_BASE}/bank/messaging/status`, {
    headers: getHeaders(true),
  });
  const resData = await response.json();
  if (!response.ok) {
    throw new Error(resData.detail || 'Failed to fetch broker status.');
  }
  return resData;
};

export const fetchQueueStatus = async () => {
  const response = await fetch(`${API_BASE}/bank/messaging/queues`, {
    headers: getHeaders(true),
  });
  const resData = await response.json();
  if (!response.ok) {
    throw new Error(resData.detail || 'Failed to fetch queues status.');
  }
  return resData;
};

export const fetchCommunicationStats = async () => {
  const response = await fetch(`${API_BASE}/bank/messaging/statistics`, {
    headers: getHeaders(true),
  });
  const resData = await response.json();
  if (!response.ok) {
    throw new Error(resData.detail || 'Failed to fetch communication statistics.');
  }
  return resData;
};

export const fetchEventHistory = async ({
  requestId = '',
  agentId = '',
  eventType = '',
  page = 1,
  pageSize = 20,
} = {}) => {
  const params = new URLSearchParams();
  if (requestId) params.append('request_id', requestId);
  if (agentId) params.append('agent_id', agentId);
  if (eventType) params.append('event_type', eventType);
  params.append('page', page);
  params.append('page_size', pageSize);

  const response = await fetch(`${API_BASE}/bank/messaging/events?${params.toString()}`, {
    headers: getHeaders(true),
  });
  const resData = await response.json();
  if (!response.ok) {
    throw new Error(resData.detail || 'Failed to fetch agent event history.');
  }
  return resData;
};

export const fetchRequestTimeline = async (requestId) => {
  const response = await fetch(`${API_BASE}/bank/messaging/events/${encodeURIComponent(requestId)}`, {
    headers: getHeaders(true),
  });
  const resData = await response.json();
  if (!response.ok) {
    throw new Error(resData.detail || 'Failed to fetch request event timeline.');
  }
  return resData;
};

export const fetchDeadLetters = async () => {
  const response = await fetch(`${API_BASE}/bank/messaging/dead-letter`, {
    headers: getHeaders(true),
  });
  const resData = await response.json();
  if (!response.ok) {
    throw new Error(resData.detail || 'Failed to fetch dead letter messages.');
  }
  return resData;
};

export const retryDeadLetterMessage = async (messageId) => {
  const response = await fetch(`${API_BASE}/bank/messaging/retry/${encodeURIComponent(messageId)}`, {
    method: 'POST',
    headers: getHeaders(true),
  });
  const resData = await response.json();
  if (!response.ok) {
    throw new Error(resData.detail || 'Failed to retry message.');
  }
  return resData;
};

export const fetchAgentCommunicationMetrics = async () => {
  const response = await fetch(`${API_BASE}/bank/agents/communication`, {
    headers: getHeaders(true),
  });
  const resData = await response.json();
  if (!response.ok) {
    throw new Error(resData.detail || 'Failed to fetch agent communication metrics.');
  }
  return resData;
};

// ============================================================================
// PHASE 7: ADMINISTRATOR & SECURITY STATUS
// ============================================================================

export const fetchAdminUsers = async ({ page = 1, pageSize = 20, role = '' } = {}) => {
  const params = new URLSearchParams();
  params.append('page', page);
  params.append('page_size', pageSize);
  if (role) params.append('role', role);

  const response = await fetch(`${API_BASE}/bank/admin/users?${params.toString()}`, {
    headers: getHeaders(true),
  });
  handleAuthResponse(response);
  const resData = await response.json();
  if (!response.ok) {
    throw new Error(resData.detail || 'Failed to fetch system users.');
  }
  return resData;
};

export const updateUserRole = async (userId, role) => {
  const response = await fetch(`${API_BASE}/bank/admin/users/${userId}/role`, {
    method: 'PUT',
    headers: getHeaders(true),
    body: JSON.stringify({ role }),
  });
  handleAuthResponse(response);
  const resData = await response.json();
  if (!response.ok) {
    throw new Error(resData.detail || 'Failed to update user role.');
  }
  return resData;
};

export const fetchSecurityStatus = async () => {
  const response = await fetch(`${API_BASE}/bank/admin/security-status`, {
    headers: getHeaders(true),
  });
  handleAuthResponse(response);
  const resData = await response.json();
  if (!response.ok) {
    throw new Error(resData.detail || 'Failed to fetch security architecture status.');
  }
  return resData;
};

// ============================================================================
// PHASE 8: AGENT FAILURE RECOVERY & FAULT TOLERANCE
// ============================================================================

export const fetchRecoveryDashboard = async () => {
  const response = await fetch(`${API_BASE}/bank/recovery/dashboard`, {
    headers: getHeaders(true),
  });
  handleAuthResponse(response);
  const resData = await response.json();
  if (!response.ok) {
    throw new Error(resData.detail || 'Failed to fetch recovery dashboard metrics.');
  }
  return resData;
};

export const fetchFailureRecords = async ({ page = 1, pageSize = 20 } = {}) => {
  const response = await fetch(`${API_BASE}/bank/recovery/failures?page=${page}&page_size=${pageSize}`, {
    headers: getHeaders(true),
  });
  handleAuthResponse(response);
  const resData = await response.json();
  if (!response.ok) {
    throw new Error(resData.detail || 'Failed to fetch failure records.');
  }
  return resData;
};

export const triggerHealthInspection = async () => {
  const response = await fetch(`${API_BASE}/bank/recovery/inspect`, {
    method: 'POST',
    headers: getHeaders(true),
  });
  handleAuthResponse(response);
  const resData = await response.json();
  if (!response.ok) {
    throw new Error(resData.detail || 'Failed to trigger health inspection.');
  }
  return resData;
};

export const manualRetryTask = async (requestId) => {
  const response = await fetch(`${API_BASE}/bank/recovery/tasks/${requestId}/retry`, {
    method: 'POST',
    headers: getHeaders(true),
  });
  handleAuthResponse(response);
  const resData = await response.json();
  if (!response.ok) {
    throw new Error(resData.detail || 'Failed to manually retry task.');
  }
  return resData;
};

export const manualReassignTask = async (requestId, targetAgentCode) => {
  const response = await fetch(`${API_BASE}/bank/recovery/tasks/${requestId}/reassign`, {
    method: 'POST',
    headers: getHeaders(true),
    body: JSON.stringify({ target_agent_code: targetAgentCode }),
  });
  handleAuthResponse(response);
  const resData = await response.json();
  if (!response.ok) {
    throw new Error(resData.detail || 'Failed to manually reassign task.');
  }
  return resData;
};

export const resetAgentHealth = async (agentCode) => {
  const response = await fetch(`${API_BASE}/bank/recovery/agents/${agentCode}/reset`, {
    method: 'POST',
    headers: getHeaders(true),
  });
  handleAuthResponse(response);
  const resData = await response.json();
  if (!response.ok) {
    throw new Error(resData.detail || 'Failed to reset agent health.');
  }
  return resData;
};

export const pauseAgent = async (agentCode) => {
  const response = await fetch(`${API_BASE}/bank/recovery/agents/${agentCode}/pause`, {
    method: 'POST',
    headers: getHeaders(true),
  });
  handleAuthResponse(response);
  const resData = await response.json();
  if (!response.ok) {
    throw new Error(resData.detail || 'Failed to pause agent.');
  }
  return resData;
};

export const resumeAgent = async (agentCode) => {
  const response = await fetch(`${API_BASE}/bank/recovery/agents/${agentCode}/resume`, {
    method: 'POST',
    headers: getHeaders(true),
  });
  handleAuthResponse(response);
  const resData = await response.json();
  if (!response.ok) {
    throw new Error(resData.detail || 'Failed to resume agent.');
  }
  return resData;
};

export const fetchCircuitBreakerStatus = async () => {
  const response = await fetch(`${API_BASE}/bank/recovery/circuit-breaker`, {
    headers: getHeaders(true),
  });
  handleAuthResponse(response);
  const resData = await response.json();
  if (!response.ok) {
    throw new Error(resData.detail || 'Failed to fetch circuit breaker status.');
  }
  return resData;
};

export const resetCircuitBreaker = async () => {
  const response = await fetch(`${API_BASE}/bank/recovery/circuit-breaker/reset`, {
    method: 'POST',
    headers: getHeaders(true),
  });
  handleAuthResponse(response);
  const resData = await response.json();
  if (!response.ok) {
    throw new Error(resData.detail || 'Failed to reset circuit breaker.');
  }
  return resData;
};

export const simulateAgentCrash = async (agentCode, reason) => {
  const response = await fetch(`${API_BASE}/bank/recovery/simulation/crash`, {
    method: 'POST',
    headers: getHeaders(true),
    body: JSON.stringify({ agent_code: agentCode, reason }),
  });
  handleAuthResponse(response);
  const resData = await response.json();
  if (!response.ok) {
    throw new Error(resData.detail || 'Failed to simulate agent crash.');
  }
  return resData;
};

export const simulateMissedHeartbeat = async (agentCode, secondsAgo = 60.0) => {
  const response = await fetch(`${API_BASE}/bank/recovery/simulation/missed-heartbeat`, {
    method: 'POST',
    headers: getHeaders(true),
    body: JSON.stringify({ agent_code: agentCode, seconds_ago: secondsAgo }),
  });
  handleAuthResponse(response);
  const resData = await response.json();
  if (!response.ok) {
    throw new Error(resData.detail || 'Failed to simulate missed heartbeat.');
  }
  return resData;
};

export const simulateRabbitMQOutage = async () => {
  const response = await fetch(`${API_BASE}/bank/recovery/simulation/rabbitmq-outage`, {
    method: 'POST',
    headers: getHeaders(true),
  });
  handleAuthResponse(response);
  const resData = await response.json();
  if (!response.ok) {
    throw new Error(resData.detail || 'Failed to simulate RabbitMQ outage.');
  }
  return resData;
};

export const simulateRabbitMQRestore = async () => {
  const response = await fetch(`${API_BASE}/bank/recovery/simulation/rabbitmq-restore`, {
    method: 'POST',
    headers: getHeaders(true),
  });
  handleAuthResponse(response);
  const resData = await response.json();
  if (!response.ok) {
    throw new Error(resData.detail || 'Failed to restore RabbitMQ dependency.');
  }
  return resData;
};

export const simulateRetryExhaustion = async (requestId) => {
  const response = await fetch(`${API_BASE}/bank/recovery/simulation/exhaust-retries/${requestId}`, {
    method: 'POST',
    headers: getHeaders(true),
  });
  handleAuthResponse(response);
  const resData = await response.json();
  if (!response.ok) {
    throw new Error(resData.detail || 'Failed to simulate retry exhaustion.');
  }
  return resData;
};

// ============================================================================
// PHASE 10: MULTI-BRANCH FEDERATION ENDPOINTS
// ============================================================================

export const fetchFederatedBranches = async () => {
  const response = await fetch(`${API_BASE}/federation/branches`, {
    headers: getHeaders(true),
  });
  handleAuthResponse(response);
  const resData = await response.json();
  if (!response.ok) {
    throw new Error(resData.detail || 'Failed to fetch federated branches.');
  }
  return resData;
};

export const fetchFederationStatistics = async () => {
  const response = await fetch(`${API_BASE}/federation/statistics`, {
    headers: getHeaders(true),
  });
  handleAuthResponse(response);
  const resData = await response.json();
  if (!response.ok) {
    throw new Error(resData.detail || 'Failed to fetch federation statistics.');
  }
  return resData;
};

export const fetchFederationEvents = async (params = {}) => {
  const query = new URLSearchParams(params).toString();
  const url = `${API_BASE}/federation/events${query ? `?${query}` : ''}`;
  const response = await fetch(url, {
    headers: getHeaders(true),
  });
  handleAuthResponse(response);
  const resData = await response.json();
  if (!response.ok) {
    throw new Error(resData.detail || 'Failed to fetch federation events.');
  }
  return resData;
};

export const triggerCrossBranchExchange = async (payload) => {
  const response = await fetch(`${API_BASE}/federation/exchange`, {
    method: 'POST',
    headers: getHeaders(true),
    body: JSON.stringify(payload),
  });
  handleAuthResponse(response);
  const resData = await response.json();
  if (!response.ok) {
    throw new Error(resData.detail || 'Failed to execute cross-branch exchange.');
  }
  return resData;
};




