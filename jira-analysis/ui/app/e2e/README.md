# Jira Analysis E2E Tests

Playwright端到端测试，验证前端UI与后端API的集成。

## 测试覆盖

### 深度分析页面
- ✅ 页面加载和UI元素
- ✅ 输入验证
- ✅ 分析流程启动
- ✅ 进度显示
- ✅ 结果展示
- ✅ SSE流式传输

### 批量分析页面
- ✅ 页面加载和配置面板
- ✅ Issue keys 添加/删除
- ✅ 分析模式切换
- ✅ 批量分析启动
- ✅ 进度跟踪
- ✅ 结果和导出选项

### API集成
- ✅ 深度分析API调用
- ✅ 批量分析API调用
- ✅ CORS配置
- ✅ 错误处理

### 响应式设计
- ✅ 移动端视口
- ✅ 平板视口

## 前置条件

1. **后端服务器运行中**
   ```bash
   cd jira-analysis
   uv run python -m src.api_server
   # 运行在 http://localhost:4501
   ```

2. **前端开发服务器运行中**
   ```bash
   cd jira-analysis/ui/app
   npm run dev
   # 运行在 http://localhost:3001
   ```

3. **测试数据**
   - 需要有效的Jira issue keys (如 KAN-9, KAN-14)
   - 后端需要配置正确的Jira连接

## 安装

```bash
cd jira-analysis/ui/app

# 安装Playwright
npm install -D @playwright/test

# 安装浏览器
npx playwright install
```

## 运行测试

```bash
# 运行所有测试
npm run test:e2e

# 使用UI模式运行（推荐）
npm run test:e2e:ui

# 有头模式运行（查看浏览器）
npm run test:e2e:headed

# 调试模式
npm run test:e2e:debug

# 运行特定测试
npx playwright test --grep "Deep Analysis"

# 运行特定浏览器
npx playwright test --project=chromium
```

## 测试结果

测试结果保存在：
- HTML报告: `playwright-report/index.html`
- JSON结果: `test-results/results.json`
- 失败截图: `test-results/`
- 失败视频: `test-results/`

查看HTML报告：
```bash
npx playwright show-report
```

## 配置

测试配置在 `playwright.config.ts`：
- 自动启动后端和前端服务器
- 失败时自动截图和录制视频
- 支持多浏览器测试
- 支持移动端测试

## 测试场景

### 1. 深度分析流程
```typescript
test('should complete deep analysis workflow', async ({ page }) => {
  // 1. 访问页面
  // 2. 输入issue key
  // 3. 点击分析
  // 4. 等待进度
  // 5. 验证结果
});
```

### 2. 批量分析流程
```typescript
test('should complete batch analysis workflow', async ({ page }) => {
  // 1. 访问批量分析页面
  // 2. 添加多个issue keys
  // 3. 选择分析模式
  // 4. 启动批量分析
  // 5. 验证进度和结果
});
```

### 3. SSE流式传输
```typescript
test('should handle SSE streaming', async ({ page }) => {
  // 1. 监听网络请求
  // 2. 启动分析
  // 3. 验证SSE连接
  // 4. 验证事件流
});
```

## 故障排查

### 测试超时
- 增加timeout: `test.setTimeout(60000)`
- 检查后端服务器是否运行
- 检查Jira连接配置

### 元素未找到
- 检查选择器是否正确
- 使用 `--headed` 模式查看浏览器
- 使用 `--debug` 模式逐步调试

### API错误
- 检查 `http://localhost:4501/health`
- 查看后端日志
- 验证CORS配置

## CI/CD集成

在CI环境中运行：
```bash
# 设置CI环境变量
export CI=true

# 运行测试
npm run test:e2e

# 测试会自动：
# - 启动服务器
# - 运行测试
# - 生成报告
# - 失败时重试2次
```

## 最佳实践

1. **独立测试**: 每个测试应该独立，不依赖其他测试
2. **清理状态**: 使用 `beforeEach` 重置状态
3. **等待策略**: 使用 `waitFor` 而不是固定延迟
4. **选择器**: 优先使用语义化选择器（text, role）
5. **断言**: 使用明确的断言消息

## 扩展测试

添加新测试：
```typescript
test('should test new feature', async ({ page }) => {
  await page.goto('/');
  // 测试逻辑
  await expect(page.locator('...')).toBeVisible();
});
```

## 参考

- [Playwright文档](https://playwright.dev)
- [测试最佳实践](https://playwright.dev/docs/best-practices)
- [选择器指南](https://playwright.dev/docs/selectors)
