"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/components/auth/auth-provider";

export default function EntryPage() {
  const router = useRouter();
  const { user, status } = useAuth();
  useEffect(() => {
    if (status === "authenticated" && user) router.replace(user.default_landing);
    if (status === "unauthenticated" || status === "error") router.replace("/login");
  }, [router, status, user]);
  return <main className="state-page" aria-busy="true"><div className="state-panel"><span className="spinner" /><h1>正在进入工作台</h1><p>正在确认会话与访问范围…</p></div></main>;
}
