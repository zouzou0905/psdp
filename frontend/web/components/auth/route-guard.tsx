"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { canAccessPath } from "@/config/access-control";
import { useAuth } from "@/components/auth/auth-provider";

export function RouteGuard({ pathname, children }: { pathname: string; children: React.ReactNode }) {
  const router = useRouter();
  const { user, status, error, refresh } = useAuth();
  useEffect(() => { if (status === "unauthenticated") router.replace(`/login?next=${encodeURIComponent(pathname)}`); }, [pathname, router, status]);
  if (status === "loading" || status === "unauthenticated") return <main className="state-page" aria-busy="true"><div className="state-panel"><span className="spinner" /><h1>正在加载权限</h1><p>正在确认账号、板块与数据范围…</p></div></main>;
  if (status === "error") return <main className="state-page"><div className="state-panel state-panel-error"><span className="state-symbol">!</span><h1>权限加载失败</h1><p>{error}</p><button className="primary-button" onClick={() => void refresh()}>重新加载</button></div></main>;
  if (!user || !canAccessPath(user, pathname)) return <main className="state-page"><div className="state-panel state-panel-error"><span className="state-symbol">403</span><h1>没有访问权限</h1><p>当前账号未获此板块或动作权限。正式授权仍由后端执行。</p><button className="primary-button" onClick={() => router.replace(user?.default_landing ?? "/login")}>返回我的工作台</button></div></main>;
  return children;
}
