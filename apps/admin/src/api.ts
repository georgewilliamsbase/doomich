// Клиент админ-API. Токен живёт только в sessionStorage вкладки и пропадает при её закрытии.

export class ApiError extends Error {
  code: string;
  status: number;
  details: Record<string, unknown>;

  constructor(code: string, message: string, status: number, details: Record<string, unknown> = {}) {
    super(message);
    this.code = code;
    this.status = status;
    this.details = details;
  }
}

const TOKEN_KEY = 'doomich.admin.token';
const BASE = '/admin/v1';

export const tokenStore = {
  get: (): string | null => sessionStorage.getItem(TOKEN_KEY),
  set: (t: string) => sessionStorage.setItem(TOKEN_KEY, t),
  clear: () => sessionStorage.removeItem(TOKEN_KEY),
};

let onUnauthorized: () => void = () => {};
export function setUnauthorizedHandler(fn: () => void) {
  onUnauthorized = fn;
}

async function request<T>(method: string, path: string, body?: unknown, raw = false): Promise<T> {
  const headers: Record<string, string> = {};
  const token = tokenStore.get();
  if (token) headers.Authorization = `Bearer ${token}`;
  let payload: BodyInit | undefined;
  if (body instanceof FormData) {
    payload = body;
  } else if (body !== undefined) {
    headers['Content-Type'] = 'application/json';
    payload = JSON.stringify(body);
  }
  const resp = await fetch(`${BASE}${path}`, { method, headers, body: payload });
  if (resp.status === 401) {
    tokenStore.clear();
    onUnauthorized();
  }
  if (!resp.ok) {
    let err: any = {};
    try {
      err = (await resp.json()).error ?? {};
    } catch {
      // тело не JSON
    }
    throw new ApiError(err.code ?? `http_${resp.status}`, err.message ?? resp.statusText, resp.status, err.details);
  }
  if (raw) return (await resp.blob()) as T;
  if (resp.status === 204) return undefined as T;
  return (await resp.json()) as T;
}

export const api = {
  get: <T>(path: string) => request<T>('GET', path),
  post: <T>(path: string, body?: unknown) => request<T>('POST', path, body),
  put: <T>(path: string, body?: unknown) => request<T>('PUT', path, body),
  patch: <T>(path: string, body?: unknown) => request<T>('PATCH', path, body),
  del: <T>(path: string) => request<T>('DELETE', path),
  blob: (path: string) => request<Blob>('GET', path, undefined, true),
};

export async function download(path: string, filename: string) {
  const blob = await api.blob(path);
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export function errorText(e: unknown): string {
  if (e instanceof ApiError) {
    const fields = (e.details?.fields as { field: string; msg: string }[] | undefined) ?? [];
    return fields.length ? `${e.message}: ${fields.map((f) => `${f.field} ${f.msg}`).join(', ')}` : e.message;
  }
  return String(e);
}

export type Admin = { id: string; login: string; role: 'superadmin' | 'tenant_admin' | 'operator'; tenant_id: string | null };
export type Tenant = {
  id: string; slug: string; name: string; short_name: string | null; timezone: string; default_locale: string;
  settings: Record<string, any>; is_active: boolean; created_at: string;
};
export type Group = { id: string; code: string; name: string | null; faculty: string | null; year: number | null; subgroups: string[]; is_active: boolean };
export type Campus = { id: string; name: string; address: string | null; lat: number | null; lon: number | null };
export type Term = { id: string; name: string; starts_on: string; ends_on: string; first_week_odd: boolean; holidays: string[] };
export type BatchStats = { codes?: number; activations?: number; revoked?: number };
export type Batch = {
  id: string; tenant_id: string; label: string; kind: 'register' | 'role_upgrade'; role: 'student' | 'teacher' | 'staff';
  group_id: string | null; max_uses: number; expires_on: string | null; is_beta: boolean; code_count: number;
  created_at: string; stats: BatchStats;
};
export type BatchCode = { id: string; code: string; uses: number; revoked: boolean };
export type Source = {
  id: string; name: string; kind: string; config: Record<string, any>; enabled: boolean; require_review_on_spike: boolean;
  last_sync_at: string | null; last_status: string | null; last_error: string | null; last_count: number | null;
  has_pending: boolean;
};
export type ImportReport = {
  rows_total: number; rows_ok: number; lessons: number; groups: string[];
  errors: { row: number; column: string | null; message: string }[]; errors_total: number;
  applied: boolean; sync?: Record<string, any>;
};
export type Lesson = {
  id: string; group_id: string; subgroup: string | null; subject: string; kind: string; starts_at: string; ends_at: string;
  room: string | null; note: string | null; status: 'scheduled' | 'cancelled'; source_id: string | null;
};
export type Stats = {
  users: number; dau: number; wau: number; wau_share: number; documents: number; users_with_documents_share: number;
  messages_7d: Record<string, number>; voice_share_7d: number;
  feedback_30d: { up: number; down: number; up_share: number | null };
};
export type Status = {
  env: string; mock_components: string[]; time: string; queues: Record<string, number | null>; llm_ok: boolean | null;
  documents: Record<string, number>;
  schedule_sources: { id: string; tenant_id: string; name: string; kind: string; last_status: string | null; last_sync_at: string | null; last_error: string | null }[];
  backup?: { ok?: boolean; finished_at?: string; snapshot?: string; size_bytes?: number; message?: string; error?: string };
  grafana_url: string;
};
export type FeedbackItem = {
  id: string; rating: number; comment: string | null; category: string | null; model_version: string | null; mode: string | null;
  question: string | null; answer: string | null; created_on: string;
};
export type AuditItem = {
  id: number; admin: string | null; action: string; object_type: string | null; object_id: string | null;
  tenant_id: string | null; details: Record<string, any> | null; created_at: string;
};
export type Release = {
  id: string; app: 'mobile' | 'desktop'; platform: string; channel: 'stable' | 'beta'; version: string; build: number;
  url: string; sha256: string; min_supported_build: number; published_at: string;
};
export type Binding = {
  id: string; tenant_id: string | null; campus_id: string | null; component: string; model_ref: string;
  stage: 'canary' | 'production'; traffic_pct: number; params: Record<string, any>; updated_at: string;
};
export type AdminRow = Admin & { totp_enabled: boolean; disabled: boolean };
