import Link from "next/link";

export default function ForbiddenPage() {
  return <main className="state-page"><div className="state-panel state-panel-error"><span className="state-symbol">403</span><h1>没有访问权限</h1><p>当前岗位无权查看此页面。前端已阻止展示，但正式授权仍由后端校验。</p><Link className="primary-button link-button" href="/">返回我的工作台</Link></div></main>;
}
