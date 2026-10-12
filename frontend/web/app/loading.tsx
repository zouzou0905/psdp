export default function Loading() {
  return (
    <main className="state-page" aria-busy="true" aria-label="正在加载工作台">
      <div className="state-panel">
        <span className="spinner" aria-hidden="true" />
        <h1>正在加载工作台</h1>
        <p>正在获取经营项目与任务状态…</p>
      </div>
    </main>
  );
}
