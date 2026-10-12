export const AUTH_UNAUTHORIZED_EVENT = "ai-ops:unauthorized";

export class ApiClient {
  constructor(private readonly baseUrl: string) {}

  get<T>(path: string): Promise<T> { return this.request<T>(path, { method: "GET" }); }
  post<TResponse, TBody = undefined>(path: string, body?: TBody): Promise<TResponse> {
    return this.request<TResponse>(path, { method: "POST", body: body === undefined ? undefined : JSON.stringify(body) });
  }
  put<TResponse, TBody>(path: string, body: TBody): Promise<TResponse> {
    return this.request<TResponse>(path, { method: "PUT", body: JSON.stringify(body) });
  }

  private async request<T>(path: string, init: RequestInit): Promise<T> {
    let response: Response;
    try {
      response = await fetch(`${this.baseUrl}${path}`, {
        ...init,
        headers: { Accept: "application/json", ...(init.body ? { "Content-Type": "application/json" } : {}) },
        cache: "no-store",
        credentials: "include",
        signal: AbortSignal.timeout(8_000),
      });
    } catch (cause) {
      throw new ApiError(0, path, "无法连接后端服务，请确认后端和数据库已启动。", { cause });
    }
    if (!response.ok) {
      if (response.status === 401 && typeof window !== "undefined") window.dispatchEvent(new Event(AUTH_UNAUTHORIZED_EVENT));
      let detail = "";
      try {
        const payload = await response.json() as { detail?: string };
        detail = typeof payload.detail === "string" ? payload.detail : "";
      } catch { /* response body is optional */ }
      throw new ApiError(response.status, path, detail || `请求失败（${response.status}）`);
    }
    return response.status === 204 ? (undefined as T) : response.json() as Promise<T>;
  }
}

export class ApiError extends Error {
  constructor(public readonly status: number, public readonly path: string, message: string, options?: ErrorOptions) {
    super(message, options);
    this.name = "ApiError";
  }
}

export function createApiClient(): ApiClient {
  return new ApiClient(process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ?? "");
}
