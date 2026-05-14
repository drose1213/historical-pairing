const DEFAULT_TIMEOUT = 30000;
const MAX_RETRIES = 2;

export class ApiError extends Error {
  constructor(
    message: string,
    public statusCode: number,
    public code?: string
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export class NetworkError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "NetworkError";
  }
}

export class TimeoutError extends Error {
  constructor(message: string = "请求超时") {
    super(message);
    this.name = "TimeoutError";
  }
}

export class RateLimitError extends Error {
  constructor(message: string = "请求过于频繁，请稍后再试") {
    super(message);
    this.name = "RateLimitError";
  }
}

const parseError = async (response: Response) => {
  try {
    const body = await response.json();
    return {
      message: body.detail || "请求失败",
      code: body.code,
    };
  } catch {
    return { message: "请求失败", code: undefined };
  }
};

const getToken = () => localStorage.getItem("token");

const authHeaders = (): Record<string, string> => {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
};

const createAbortController = (timeout: number): AbortController => {
  const controller = new AbortController();
  setTimeout(() => controller.abort(), timeout);
  return controller;
};

interface FetchOptions extends RequestInit {
  timeout?: number;
  retries?: number;
}

async function fetchWithTimeout(
  url: string,
  options: FetchOptions = {}
): Promise<Response> {
  const { timeout = DEFAULT_TIMEOUT, retries = 0, ...fetchOptions } = options;
  const controller = createAbortController(timeout);
  let lastError: Error;

  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      const response = await fetch(url, {
        ...fetchOptions,
        signal: controller.signal,
      });

      if (response.status === 429) {
        const { message } = await parseError(response);
        throw new RateLimitError(message);
      }

      return response;
    } catch (error) {
      lastError = error as Error;

      if (error instanceof RateLimitError) {
        throw error;
      }

      if (error instanceof Error && error.name === "AbortError") {
        lastError = new TimeoutError();
      }

      if (attempt < retries) {
        await new Promise((resolve) => setTimeout(resolve, 1000 * (attempt + 1)));
      }
    }
  }

  throw lastError!;
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (response.ok) {
    return response.json();
  }

  const { message, code } = await parseError(response);

  if (response.status === 401) {
    localStorage.removeItem("token");
    window.dispatchEvent(new Event("auth:unauthorized"));
  }

  throw new ApiError(message, response.status, code);
}

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
  final_score: number;
  correct_count: number;
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

export interface CaptchaData {
  token: string;
  question: string;
  expires_in: number;
}

export async function getCaptcha(): Promise<CaptchaData> {
  const response = await fetchWithTimeout("/api/auth/captcha", {
    timeout: 10000,
  });
  return handleResponse<CaptchaData>(response);
}

export async function sendCode(
  email: string,
  captchaToken: string,
  captchaAnswer: string
): Promise<void> {
  const response = await fetchWithTimeout("/api/auth/send-code", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, captcha_token: captchaToken, captcha_answer: captchaAnswer }),
    timeout: 15000,
    retries: 1,
  });
  return handleResponse<void>(response);
}

export async function register(
  email: string,
  code: string,
  password: string
): Promise<AuthResponse> {
  const response = await fetchWithTimeout("/api/auth/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, code, password }),
    timeout: 20000,
    retries: 1,
  });
  return handleResponse<AuthResponse>(response);
}

export async function login(email: string, password: string): Promise<AuthResponse> {
  const response = await fetchWithTimeout("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
    timeout: 20000,
    retries: 1,
  });
  return handleResponse<AuthResponse>(response);
}

export async function getMe(): Promise<User> {
  const response = await fetchWithTimeout("/api/auth/me", {
    headers: { ...authHeaders() },
    timeout: 10000,
  });
  return handleResponse<User>(response);
}

// ============ Games ============

export async function createGame(keyword: string): Promise<CreateGameResponse> {
  const response = await fetchWithTimeout("/api/games", {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({ keyword }),
    timeout: 60000,
    retries: 1,
  });
  return handleResponse<CreateGameResponse>(response);
}

export async function submitGame(
  gameId: string,
  matches: Array<{ leftId: string; rightId: string }>,
  timeUsed?: number,
  timeUp?: boolean
): Promise<SubmitResponse> {
  const response = await fetchWithTimeout(`/api/games/${gameId}/submit`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({ matches, time_used: timeUsed ?? null, time_up: timeUp ?? false }),
    timeout: 30000,
    retries: 1,
  });
  return handleResponse<SubmitResponse>(response);
}

// ============ Leaderboard ============

export interface LeaderboardItem {
  rank: number;
  email: string;
  total_games: number;
  avg_score: number;
  best_score: number;
  total_correct: number;
}

export interface LeaderboardResponse {
  items: LeaderboardItem[];
  total: number;
  page: number;
  page_size: number;
}

export async function getLeaderboard(
  page: number = 1,
  pageSize: number = 10,
  sortBy: "avg_score" | "total_games" | "best_score" | "total_correct" = "avg_score",
  sortOrder: "asc" | "desc" = "desc"
): Promise<LeaderboardResponse> {
  const url = `/api/leaderboard?page=${page}&page_size=${pageSize}&sort_by=${sortBy}&sort_order=${sortOrder}`;
  const response = await fetchWithTimeout(url, {
    timeout: 15000,
  });
  return handleResponse<LeaderboardResponse>(response);
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
  const response = await fetchWithTimeout(`/api/history?page=${page}&page_size=${pageSize}`, {
    headers: { ...authHeaders() },
    timeout: 15000,
  });
  return handleResponse<HistoryListResponse>(response);
}

export async function getHistoryDetail(gameId: string): Promise<HistoryDetailResponse> {
  const response = await fetchWithTimeout(`/api/history/${gameId}`, {
    headers: { ...authHeaders() },
    timeout: 15000,
  });
  return handleResponse<HistoryDetailResponse>(response);
}

export interface PeriodStats {
  keyword: string;
  count: number;
  avg_score: number;
}

export interface PairTypeStats {
  pair_type: string;
  total: number;
  correct: number;
  correct_rate: number;
}

export interface UserStatsResponse {
  total_games: number;
  avg_score: number;
  min_score: number;
  max_score: number;
  avg_time: number | null;
  min_time: number | null;
  max_time: number | null;
  periods: PeriodStats[];
  pair_types: PairTypeStats[];
  tendency: string;
}

export async function getUserStats(): Promise<UserStatsResponse> {
  const response = await fetchWithTimeout("/api/history/stats", {
    headers: { ...authHeaders() },
    timeout: 15000,
  });
  return handleResponse<UserStatsResponse>(response);
}

export interface RecentKeywordsResponse {
  keywords: string[];
}

export async function getRecentKeywords(): Promise<RecentKeywordsResponse> {
  const response = await fetchWithTimeout("/api/history/recent-keywords", {
    headers: { ...authHeaders() },
    timeout: 10000,
  });
  return handleResponse<RecentKeywordsResponse>(response);
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
  const response = await fetchWithTimeout("/api/admin/stats", {
    headers: { ...authHeaders() },
    timeout: 15000,
  });
  return handleResponse<AdminStats>(response);
}

export async function getAdminUsers(
  page: number = 1,
  pageSize: number = 10
): Promise<UserListResponse> {
  const response = await fetchWithTimeout(`/api/admin/users?page=${page}&page_size=${pageSize}`, {
    headers: { ...authHeaders() },
    timeout: 15000,
  });
  return handleResponse<UserListResponse>(response);
}

export async function getAdminGames(
  page: number = 1,
  pageSize: number = 10
): Promise<GameListResponse> {
  const response = await fetchWithTimeout(`/api/admin/games?page=${page}&page_size=${pageSize}`, {
    headers: { ...authHeaders() },
    timeout: 15000,
  });
  return handleResponse<GameListResponse>(response);
}

export async function getAdminConfigs(): Promise<ConfigItem[]> {
  const response = await fetchWithTimeout("/api/admin/configs", {
    headers: { ...authHeaders() },
    timeout: 10000,
  });
  return handleResponse<ConfigItem[]>(response);
}

export async function updateAdminConfig(key: string, value: string): Promise<ConfigItem> {
  const response = await fetchWithTimeout(`/api/admin/configs/${encodeURIComponent(key)}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({ value }),
    timeout: 15000,
    retries: 1,
  });
  return handleResponse<ConfigItem>(response);
}

// ============ Configs (Local) ============

export async function listConfigs(): Promise<ConfigItem[]> {
  const response = await fetchWithTimeout("/api/configs", {
    timeout: 10000,
  });
  return handleResponse<ConfigItem[]>(response);
}

export async function updateConfig(key: string, value: string): Promise<ConfigItem> {
  const response = await fetchWithTimeout(`/api/configs/${encodeURIComponent(key)}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ key, value }),
    timeout: 15000,
    retries: 1,
  });
  return handleResponse<ConfigItem>(response);
}

// ============ Analytics ============

export async function trackEvent(
  eventType: string,
  gameId?: string,
  payload?: Record<string, unknown>
): Promise<void> {
  try {
    await fetchWithTimeout("/api/analytics/track", {
      method: "POST",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify({ event_type: eventType, game_id: gameId, payload }),
      timeout: 5000,
    });
  } catch {
    // Silently fail for analytics tracking
  }
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
