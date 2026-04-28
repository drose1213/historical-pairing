const parseError = async (response: Response) => {
  try {
    const body = await response.json();
    return body.detail || "请求失败";
  } catch {
    return "请求失败";
  }
};

const getToken = () => localStorage.getItem("token");

const authHeaders = () => {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
};

// ============ Types ============

export type PairItem = {
  id: string;
  text: string;
};

export type CreateGameResponse = {
  gameId: string;
  keyword: string;
  leftItems: PairItem[];
  rightItems: PairItem[];
};

export type SubmitResponse = {
  score: number;
  total: number;
  results: Array<{
    leftId: string;
    left: string;
    userRight: string | null;
    correctRight: string;
    isCorrect: boolean;
    explanation: string;
    type: string;
  }>;
};

export type ConfigItem = {
  key: string;
  value: string | null;
  description: string | null;
  configured: boolean;
};

// ============ Auth ============

export interface User {
  id: string;
  email: string;
  isAdmin: boolean;
}

interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export async function sendCode(email: string): Promise<void> {
  const response = await fetch("/api/auth/send-code", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email }),
  });
  if (!response.ok) {
    throw new Error(await parseError(response));
  }
}

export async function register(
  email: string,
  code: string,
  password: string
): Promise<AuthResponse> {
  const response = await fetch("/api/auth/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, code, password }),
  });
  if (!response.ok) {
    throw new Error(await parseError(response));
  }
  return response.json();
}

export async function login(email: string, password: string): Promise<AuthResponse> {
  const response = await fetch("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!response.ok) {
    throw new Error(await parseError(response));
  }
  return response.json();
}

export async function getMe(): Promise<User> {
  const response = await fetch("/api/auth/me", {
    headers: { ...authHeaders() },
  });
  if (!response.ok) {
    throw new Error(await parseError(response));
  }
  return response.json();
}

// ============ Games ============

export async function createGame(keyword: string): Promise<CreateGameResponse> {
  const response = await fetch("/api/games", {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({ keyword }),
  });
  if (!response.ok) {
    throw new Error(await parseError(response));
  }
  return response.json();
}

export async function submitGame(
  gameId: string,
  matches: Array<{ leftId: string; rightId: string }>
): Promise<SubmitResponse> {
  const response = await fetch(`/api/games/${gameId}/submit`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({ matches }),
  });
  if (!response.ok) {
    throw new Error(await parseError(response));
  }
  return response.json();
}

// ============ History ============

export interface HistoryItem {
  id: string;
  keyword: string;
  score: number | null;
  total: number;
  time_used: number | null;
  created_at: string;
}

export interface HistoryListResponse {
  items: HistoryItem[];
  total: number;
  page: number;
  page_size: number;
}

export interface HistoryDetailResult {
  left: string;
  right: string;
  correct_right: string;
  is_correct: boolean;
  explanation: string;
  type: string;
}

export interface HistoryDetailResponse {
  id: string;
  keyword: string;
  score: number | null;
  total: number;
  time_used: number | null;
  status: string;
  created_at: string;
  submitted_at: string | null;
  results: HistoryDetailResult[];
}

export async function getHistory(
  page: number = 1,
  pageSize: number = 10
): Promise<HistoryListResponse> {
  const response = await fetch(`/api/history?page=${page}&page_size=${pageSize}`, {
    headers: { ...authHeaders() },
  });
  if (!response.ok) {
    throw new Error(await parseError(response));
  }
  return response.json();
}

export async function getHistoryDetail(gameId: string): Promise<HistoryDetailResponse> {
  const response = await fetch(`/api/history/${gameId}`, {
    headers: { ...authHeaders() },
  });
  if (!response.ok) {
    throw new Error(await parseError(response));
  }
  return response.json();
}

// ============ Admin ============

export interface AdminStats {
  total_users: number;
  active_users_7d: number;
  total_games: number;
  avg_correct_rate: number;
  avg_time_used: number | null;
}

export interface UserListItem {
  id: string;
  email: string;
  is_admin: boolean;
  created_at: string;
  total_games: number;
  last_game_at: string | null;
}

export interface UserListResponse {
  items: UserListItem[];
  total: number;
  page: number;
  page_size: number;
}

export interface GameListItem {
  id: string;
  user_email: string | null;
  keyword: string;
  score: number | null;
  total: number;
  time_used: number | null;
  status: string;
  created_at: string;
}

export interface GameListResponse {
  items: GameListItem[];
  total: number;
  page: number;
  page_size: number;
}

export async function getAdminStats(): Promise<AdminStats> {
  const response = await fetch("/api/admin/stats", {
    headers: { ...authHeaders() },
  });
  if (!response.ok) {
    throw new Error(await parseError(response));
  }
  return response.json();
}

export async function getAdminUsers(
  page: number = 1,
  pageSize: number = 10
): Promise<UserListResponse> {
  const response = await fetch(`/api/admin/users?page=${page}&page_size=${pageSize}`, {
    headers: { ...authHeaders() },
  });
  if (!response.ok) {
    throw new Error(await parseError(response));
  }
  return response.json();
}

export async function getAdminGames(
  page: number = 1,
  pageSize: number = 10
): Promise<GameListResponse> {
  const response = await fetch(`/api/admin/games?page=${page}&page_size=${pageSize}`, {
    headers: { ...authHeaders() },
  });
  if (!response.ok) {
    throw new Error(await parseError(response));
  }
  return response.json();
}

export async function getAdminConfigs(): Promise<ConfigItem[]> {
  const response = await fetch("/api/admin/configs", {
    headers: { ...authHeaders() },
  });
  if (!response.ok) {
    throw new Error(await parseError(response));
  }
  return response.json();
}

export async function updateAdminConfig(key: string, value: string): Promise<ConfigItem> {
  const response = await fetch(`/api/admin/configs/${encodeURIComponent(key)}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({ value }),
  });
  if (!response.ok) {
    throw new Error(await parseError(response));
  }
  return response.json();
}

// ============ Configs (Local) ============

export async function listConfigs(): Promise<ConfigItem[]> {
  const response = await fetch("/api/configs");
  if (!response.ok) {
    throw new Error(await parseError(response));
  }
  return response.json();
}

export async function updateConfig(key: string, value: string): Promise<ConfigItem> {
  const response = await fetch(`/api/configs/${encodeURIComponent(key)}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ key, value }),
  });
  if (!response.ok) {
    throw new Error(await parseError(response));
  }
  return response.json();
}

// ============ Analytics ============

export async function trackEvent(
  eventType: string,
  gameId?: string,
  payload?: Record<string, unknown>
): Promise<void> {
  await fetch("/api/analytics/track", {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({ event_type: eventType, game_id: gameId, payload }),
  });
}

// ============ API Object ============

export const api = {
  // Auth
  sendCode,
  register,
  login,
  getMe,
  // Games
  createGame,
  submitGame,
  // History
  getHistory,
  getHistoryDetail,
  // Admin
  getAdminStats,
  getAdminUsers,
  getAdminGames,
  getAdminConfigs,
  updateAdminConfig,
  // Configs
  listConfigs,
  updateConfig,
  // Analytics
  trackEvent,
};
