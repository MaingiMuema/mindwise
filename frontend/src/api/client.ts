import { clearStoredSession, getStoredSession, setStoredSession } from "../lib/storage";
import type {
  AuthSession,
  AuthUrlResponse,
  GoogleCallbackPayload,
  Job,
  JobCreatePayload,
  JobLog,
  JobStatusResponse,
  Project,
  ProjectCreatePayload,
  User,
} from "../types/api";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";

class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

async function parseError(response: Response): Promise<never> {
  let message = `Request failed with status ${response.status}`;
  try {
    const payload = (await response.json()) as { detail?: string };
    if (payload.detail) {
      message = payload.detail;
    }
  } catch {
    const text = await response.text();
    if (text) {
      message = text;
    }
  }
  throw new ApiError(message, response.status);
}

async function refreshSession(): Promise<AuthSession | null> {
  const session = getStoredSession();
  if (!session?.tokens.refresh_token) {
    return null;
  }

  const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ refresh_token: session.tokens.refresh_token }),
  });

  if (!response.ok) {
    clearStoredSession();
    return null;
  }

  const nextSession = (await response.json()) as AuthSession;
  setStoredSession(nextSession);
  return nextSession;
}

async function request<T>(
  path: string,
  init: RequestInit = {},
  options: { auth?: boolean; retry?: boolean; responseType?: "json" | "blob" } = {},
): Promise<T> {
  const { auth = true, retry = true, responseType = "json" } = options;
  const headers = new Headers(init.headers);
  const session = getStoredSession();

  if (!headers.has("Content-Type") && init.body && !(init.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  if (auth && session?.tokens.access_token) {
    headers.set("Authorization", `Bearer ${session.tokens.access_token}`);
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers,
  });

  if (response.status === 401 && auth && retry) {
    const refreshed = await refreshSession();
    if (refreshed) {
      return request<T>(path, init, { auth, retry: false, responseType });
    }
  }

  if (!response.ok) {
    return parseError(response);
  }

  if (responseType === "blob") {
    return (await response.blob()) as T;
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

export const api = {
  getGoogleLogin(redirectHint?: string) {
    const query = redirectHint
      ? `?redirect_hint=${encodeURIComponent(redirectHint)}`
      : "";
    return request<AuthUrlResponse>(`/auth/google/login${query}`, { method: "GET" }, { auth: false });
  },
  completeGoogleCallback(payload: GoogleCallbackPayload) {
    return request<AuthSession>(
      "/auth/google/callback",
      {
        method: "POST",
        body: JSON.stringify(payload),
      },
      { auth: false },
    );
  },
  getMe() {
    return request<User>("/auth/me", { method: "GET" });
  },
  listProjects() {
    return request<Project[]>("/projects", { method: "GET" });
  },
  createProject(payload: ProjectCreatePayload) {
    return request<Project>("/projects", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
  getProject(projectId: string) {
    return request<Project>(`/projects/${projectId}`, { method: "GET" });
  },
  createJob(projectId: string, payload: JobCreatePayload) {
    return request<Job>(`/projects/${projectId}/jobs`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
  getJob(jobId: string) {
    return request<JobStatusResponse>(`/jobs/${jobId}`, { method: "GET" });
  },
  getJobLogs(jobId: string) {
    return request<JobLog[]>(`/jobs/${jobId}/logs`, { method: "GET" });
  },
  retryJob(jobId: string) {
    return request<Job>(`/jobs/${jobId}/retry`, {
      method: "POST",
      body: JSON.stringify({ reset_failed_scenes: true }),
    });
  },
  rerenderScene(jobId: string, sceneId: string) {
    return request<Job>(`/jobs/${jobId}/scenes/${sceneId}/rerender`, {
      method: "POST",
      body: JSON.stringify({ diagnostics_mode: false }),
    });
  },
  async downloadExport(jobId: string) {
    const blob = await request<Blob>(`/exports/${jobId}`, { method: "GET" }, { responseType: "blob" });
    const url = window.URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `${jobId}.mp4`;
    anchor.click();
    window.URL.revokeObjectURL(url);
  },
};
