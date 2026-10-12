"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Boxes, CheckCircle2, LockKeyhole, ShieldCheck } from "lucide-react";
import { canAccessPath } from "@/config/access-control";
import { useAuth } from "@/components/auth/auth-provider";

function LoginContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { user, status, error, login } = useAuth();
  const [submitting, setSubmitting] = useState(false);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  useEffect(() => { if (status === "authenticated" && user) router.replace(user.default_landing); }, [router, status, user]);

  async function signIn(event: React.FormEvent) {
    event.preventDefault();
    setSubmitting(true);
    try {
      const current = await login({ username: username.trim(), password });
      const requested = searchParams.get("next");
      router.replace(requested && canAccessPath(current, requested) ? requested : current.default_landing);
    } catch { /* AuthProvider renders the normalized error. */ }
    finally { setSubmitting(false); }
  }

  return <main className="login-page">
    <section className="login-intro">
      <div className="login-brand"><span><Boxes /></span><strong>AI 商品运营中台</strong></div>
      <div className="login-intro-copy"><h1>用组织账号进入你的工作台</h1><p>登录后，后端会按账号返回可见板块、动作权限和店铺范围。前端不会让用户选择身份，也不会保存 Token 或权限到本地存储。</p></div>
      <ul><li><CheckCircle2 /><span>身份与授权范围由后端账号配置决定</span></li><li><CheckCircle2 /><span>高风险动作保留人工审批边界</span></li><li><CheckCircle2 /><span>任务、运行与外部回执保持可追踪</span></li></ul>
    </section>
    <section className="login-panel">
      <form onSubmit={signIn} className="credential-form">
        <div className="login-form-heading"><span><LockKeyhole /></span><div><h2>登录工作台</h2><p>使用已由管理员配置访问范围的账号。</p></div></div>
        <label>账号<input required autoFocus autoComplete="username" name="username" value={username} onChange={(event) => setUsername(event.target.value)} /></label>
        <label>密码<input required type="password" autoComplete="current-password" name="password" value={password} onChange={(event) => setPassword(event.target.value)} /></label>
        <button className="primary-button" disabled={submitting || !username.trim() || !password}>{submitting ? "正在验证…" : "登录"}</button>
      </form>
      {error ? <div className="login-error" role="alert">{error}</div> : null}
      <p className="login-footnote"><ShieldCheck /> 会话由后端 HttpOnly Cookie 管理；页面菜单仅反映已返回的权限，不替代后端授权。</p>
    </section>
  </main>;
}

export default function LoginPage() {
  return <Suspense fallback={<main className="login-page"><div className="workspace-state"><span className="spinner" /><strong>正在加载登录页</strong></div></main>}><LoginContent /></Suspense>;
}
