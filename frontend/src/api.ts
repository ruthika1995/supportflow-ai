const API_BASE = '/api/v1';

export interface Customer {
  id: number;
  name: string;
  email: string;
  phone?: string;
  address?: string;
}

export interface OrderItem {
  id: number;
  product_id: number;
  quantity: number;
  unit_price: number;
}

export interface Order {
  id: number;
  customer_id: number;
  status: string;
  total_amount: number;
  shipping_address?: string;
  tracking_number?: string;
  estimated_delivery?: string;
  items: OrderItem[];
  created_at?: string;
}

export interface MessageData {
  id: number;
  conversation_id: number;
  sender_type: string;
  sender_name?: string;
  content: string;
  tool_calls?: string;
  created_at?: string;
}

export interface Conversation {
  id: number;
  ticket_id: number;
  messages: MessageData[];
  created_at?: string;
}

export interface Ticket {
  id: number;
  customer_id: number;
  subject: string;
  status: string;
  priority: string;
  assigned_agent_id?: number;
  resolution_notes?: string;
  conversations: Conversation[];
  created_at?: string;
  updated_at?: string;
}

export interface ApprovalRequest {
  id: number;
  ticket_id: number;
  conversation_id: number;
  action_type: string;
  action_payload: string;
  risk_level: string;
  status: string;
  reviewed_by?: number;
  review_notes?: string;
  created_at?: string;
  reviewed_at?: string;
}

export interface ChatResponse {
  response: string;
  conversation_id: number;
  ticket_id: number;
  tool_calls_made: Array<{tool: string; args: Record<string, unknown>; result: Record<string, unknown>}>;
  requires_approval: boolean;
  approval_request_id?: number;
}

export interface Analytics {
  total_tickets: number;
  open_tickets: number;
  ai_resolved: number;
  human_resolved: number;
  escalated: number;
  avg_resolution_time_minutes?: number;
  ai_resolution_rate: number;
  escalation_rate: number;
  total_conversations: number;
  total_messages: number;
}

export interface KnowledgeDoc {
  id: number;
  filename: string;
  title?: string;
  category?: string;
  content: string;
  chunk_index: number;
  created_at?: string;
}

export interface Product {
  id: number;
  name: string;
  description?: string;
  price: number;
  inventory: number;
  category?: string;
}

// ─── API Functions ─────────────────────────────

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const token = localStorage.getItem('sf_token');
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options?.headers as Record<string, string> || {}),
  };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}${url}`, { ...options, headers });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: 'Request failed' }));
    throw new Error(error.detail || 'Request failed');
  }
  return res.json();
}

// Auth
export const authApi = {
  login: (email: string, password: string) =>
    request<{access_token: string; user: {id: number; email: string; full_name: string; role: string}}>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),
  register: (email: string, password: string, full_name: string, role: string) =>
    request<{access_token: string; user: {id: number; email: string; full_name: string; role: string}}>('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password, full_name, role }),
    }),
};

// Customers
export const customersApi = {
  list: () => request<Customer[]>('/customers/'),
  get: (id: number) => request<Customer>(`/customers/${id}`),
  getOrders: (id: number) => request<Order[]>(`/customers/${id}/orders`),
};

// Orders
export const ordersApi = {
  list: () => request<Order[]>('/orders/'),
  get: (id: number) => request<Order>(`/orders/${id}`),
  getStatus: (id: number) => request<{order_id: number; status: string; tracking_number?: string; estimated_delivery?: string}>(`/orders/${id}/status`),
  cancel: (id: number) => request<{order_id: number; status: string}>(`/orders/${id}/cancel`, { method: 'POST' }),
};

// Products
export const productsApi = {
  list: () => request<Product[]>('/products/'),
  get: (id: number) => request<Product>(`/products/${id}`),
};

// Tickets
export const ticketsApi = {
  list: (status?: string) => request<Ticket[]>(`/tickets/${status ? `?status=${status}` : ''}`),
  get: (id: number) => request<Ticket>(`/tickets/${id}`),
  update: (id: number, data: Partial<Ticket>) => request<Ticket>(`/tickets/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  }),
  escalate: (id: number) => request<{ticket_id: number; status: string}>(`/tickets/${id}/escalate`, { method: 'POST' }),
  listPendingApprovals: () => request<ApprovalRequest[]>('/tickets/approvals/pending'),
  reviewApproval: (id: number, status: string, notes?: string) => request<ApprovalRequest>(`/tickets/approvals/${id}/review`, {
    method: 'POST',
    body: JSON.stringify({ status, review_notes: notes }),
  }),
  addMessage: (ticket_id: number, sender_type: string, content: string, sender_name?: string) =>
    request<MessageData>(`/tickets/${ticket_id}/messages?sender_type=${sender_type}&content=${encodeURIComponent(content)}${sender_name ? `&sender_name=${encodeURIComponent(sender_name)}` : ''}`, { method: 'POST' }),
};

// AI
export const aiApi = {
  chat: (message: string, customer_id: number, conversation_id?: number) =>
    request<ChatResponse>('/ai/chat', {
      method: 'POST',
      body: JSON.stringify({ message, customer_id, conversation_id }),
    }),
};

// Knowledge
export const knowledgeApi = {
  list: () => request<KnowledgeDoc[]>('/ai/knowledge'),
  delete: (id: number) => request<{deleted: boolean}>(`/ai/knowledge/${id}`, { method: 'DELETE' }),
  addText: (filename: string, content: string, title?: string, category?: string) =>
    request<KnowledgeDoc[]>(`/ai/knowledge/text?filename=${encodeURIComponent(filename)}&content=${encodeURIComponent(content)}${title ? `&title=${encodeURIComponent(title)}` : ''}${category ? `&category=${encodeURIComponent(category)}` : ''}`, { method: 'POST' }),
};

// Analytics
export const analyticsApi = {
  overview: () => request<Analytics>('/analytics/overview'),
  byStatus: () => request<Record<string, number>>('/analytics/tickets/by-status'),
  byPriority: () => request<Record<string, number>>('/analytics/tickets/by-priority'),
};
