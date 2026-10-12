"use client";

export default function ErrorPage({ reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return (
    <main className="state-page">
      <div className="state-panel state-panel-error">
        <span className="state-symbol">!</span>
        <h1>工作台加载失败</h1>
        <p>请检查网络连接或稍后重试。系统不会在状态未知时重复提交外部动作。</p>
        <button className="primary-button" onClick={reset}>重新加载</button>
      </div>
    </main>
  );
}
