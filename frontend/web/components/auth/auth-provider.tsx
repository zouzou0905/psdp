"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { AUTH_UNAUTHORIZED_EVENT, ApiError } from "@/lib/api-client";
import { createAuthRepository, type LoginInput } from "@/repositories/auth-repository";
import type { AccessContext, AuthStatus, Store } from "@/types/auth";

interface AuthContextValue {
  user: AccessContext | null;
  stores: Store[];
  selectedStoreId: string | null;
  status: AuthStatus;
  error: string | null;
  login(input: LoginInput): Promise<AccessContext>;
  logout(): Promise<void>;
  refresh(): Promise<void>;
  selectStore(storeId: string): void;
}

const AuthContext = createContext<AuthContextValue | null>(null);
const repository = createAuthRepository();

function errorMessage(cause: unknown, fallback: string): string {
  if (cause instanceof ApiError) {
    if (cause.status === 401) return "账号或密码错误，或当前会话已失效。";
    if (cause.status === 403) return "当前账号没有执行此操作的权限。";
    if (cause.status === 0 || cause.status >= 500) return "后端服务或数据库暂不可用，请稍后重试。";
    return cause.message;
  }
  return fallback;
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AccessContext | null>(null);
  const [stores, setStores] = useState<Store[]>([]);
  const [selectedStoreId, setSelectedStoreId] = useState<string | null>(null);
  const [status, setStatus] = useState<AuthStatus>("loading");
  const [error, setError] = useState<string | null>(null);

  const clearSessionUi = useCallback(() => {
    setUser(null); setStores([]); setSelectedStoreId(null); setError(null); setStatus("unauthenticated");
  }, []);

  const loadStores = useCallback(async () => {
    const allowed = await repository.stores();
    setStores(allowed);
    setSelectedStoreId((current) => allowed.some((store) => store.store_id === current) ? current : allowed[0]?.store_id ?? null);
  }, []);

  const refresh = useCallback(async () => {
    setStatus("loading"); setError(null);
    try {
      const current = await repository.me();
      if (!current) { clearSessionUi(); return; }
      setUser(current); setStatus("authenticated");
      await loadStores();
    } catch (cause) {
      setUser(null); setStores([]); setSelectedStoreId(null);
      setError(errorMessage(cause, "会话或权限信息加载失败，请重新登录。")); setStatus("error");
    }
  }, [clearSessionUi, loadStores]);

  useEffect(() => {
    const timer = window.setTimeout(() => { void refresh(); }, 0);
    return () => window.clearTimeout(timer);
  }, [refresh]);
  useEffect(() => {
    const onUnauthorized = () => clearSessionUi();
    window.addEventListener(AUTH_UNAUTHORIZED_EVENT, onUnauthorized);
    return () => window.removeEventListener(AUTH_UNAUTHORIZED_EVENT, onUnauthorized);
  }, [clearSessionUi]);

  const login = useCallback(async (input: LoginInput) => {
    setStatus("loading"); setError(null);
    try {
      const current = await repository.login(input);
      setUser(current); setStatus("authenticated");
      await loadStores();
      return current;
    } catch (cause) {
      setUser(null); setStores([]); setSelectedStoreId(null);
      setStatus("error"); setError(errorMessage(cause, "登录失败，请重试。"));
      throw cause;
    }
  }, [loadStores]);

  const logout = useCallback(async () => {
    try { await repository.logout(); } finally { clearSessionUi(); }
  }, [clearSessionUi]);

  const selectStore = useCallback((storeId: string) => {
    if (stores.some((store) => store.store_id === storeId)) setSelectedStoreId(storeId);
  }, [stores]);

  const value = useMemo<AuthContextValue>(() => ({ user, stores, selectedStoreId, status, error, login, logout, refresh, selectStore }), [user, stores, selectedStoreId, status, error, login, logout, refresh, selectStore]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const value = useContext(AuthContext);
  if (!value) throw new Error("useAuth must be used within AuthProvider");
  return value;
}
