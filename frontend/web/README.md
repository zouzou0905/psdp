# AI 商品运营中台前端

Next.js、React、TypeScript 与 Tailwind CSS 构建的内部业务工作台。账号身份、可见板块、动作权限和店铺范围均以后端访问上下文为准；前端导航过滤不构成正式权限控制。

## 启动

在仓库根目录双击或运行 `scripts/start-dev.cmd`，也可在 PowerShell 执行：

```powershell
.\scripts\start-dev.ps1
```

脚本会启动 FastAPI（8000）和前端（3001），默认使用真实账号认证并打开 `http://localhost:3001`。保持脚本窗口开启，按 Ctrl+C 同时停止服务。

只启动前端：

```bash
cd frontend/web
npm install
npm run dev
```

## 环境变量

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_ENABLE_DEMO_AUTH=false
```

正式页面不提供角色选择，也不在 localStorage 保存用户、角色、权限或 Token。后端通过 HttpOnly Cookie 管理会话，所有 API 请求使用 `credentials: "include"`。开发与正式启动均默认关闭 Demo 认证。

已接入接口：

- `POST /api/v1/auth/login`
- `POST /api/v1/auth/logout`
- `GET /api/v1/me/access-context`
- `GET /api/v1/me/stores`
- `GET /api/v1/{operations|procurement|creative|admin}/dashboard`
- `GET /api/v1/admin/errors`
- `GET /api/v1/selection-records`
- `GET /api/v1/selection-records/{selection_id}`
- `GET/PUT /api/v1/selection-records/{selection_id}/quotation`
- `GET /api/v1/selection-records/{selection_id}/profit-review`
- `GET/PUT /api/v1/selection-records/{selection_id}/final-selection`
- `GET/PUT /api/v1/selection-records/{selection_id}/competitors`
- `GET /api/v1/selection-records/{selection_id}/ai-tasks`
- `GET /api/v1/selection-records/{selection_id}/listing-draft`

采购工具台按当前阶段展示 AI 选品、采购询价和利润复核，不读取或展示 Listing 文案；运营工作台在后端返回 `listing_copy.read` 且店铺位于授权范围时展示 Listing 文案。询价、最终复选和竞品保存使用后端修订号并处理版本冲突。当前契约没有 AI 任务启动接口和采购下单接口，因此前端只展示实际任务状态，未配置时不会模拟成功。

selection-records 列表契约未提供 `store_id` 查询参数；后端先按账号店铺范围过滤，前端店铺选择器再从 `/me/stores` 返回的授权店铺中切换当前视图，不自行扩展数据范围。

## 检查

```bash
npm run lint
npm run typecheck
npm test
npm run build
```

目录职责：`app/` 页面，`components/` 应用壳与认证状态，`config/` 集中访问策略，`lib/` API client，`repositories/` 数据访问，`types/` 契约视图类型，`artifacts/` 浏览器验证截图。
