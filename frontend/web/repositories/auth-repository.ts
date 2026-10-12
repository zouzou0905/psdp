import { ApiClient, ApiError, createApiClient } from "@/lib/api-client";
import type { AccessContext, Store } from "@/types/auth";

export interface LoginInput { username: string; password: string }
export interface AuthRepository {
  login(input: LoginInput): Promise<AccessContext>;
  logout(): Promise<void>;
  me(): Promise<AccessContext | null>;
  stores(): Promise<Store[]>;
}

export class ApiAuthRepository implements AuthRepository {
  constructor(private readonly client: ApiClient) {}
  login(input: LoginInput): Promise<AccessContext> { return this.client.post("/api/v1/auth/login", input); }
  async logout(): Promise<void> {
    try {
      await this.client.post<void>("/api/v1/auth/logout");
    } catch (cause) {
      // Logout is idempotent: an expired or already-revoked session is already logged out.
      if (cause instanceof ApiError && cause.status === 401) return;
      throw cause;
    }
  }
  async me(): Promise<AccessContext | null> {
    try { return await this.client.get<AccessContext>("/api/v1/me/access-context"); }
    catch (cause) { if (cause instanceof ApiError && cause.status === 401) return null; throw cause; }
  }
  async stores(): Promise<Store[]> {
    const response = await this.client.get<{ items: Store[]; total: number }>("/api/v1/me/stores");
    return response.items;
  }
}

export function createAuthRepository(): AuthRepository { return new ApiAuthRepository(createApiClient()); }
