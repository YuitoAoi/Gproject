---
status: testing
phase: 01-frontend-backend-infrastructure
source: []
started: 2026-04-23T05:00:00Z
updated: 2026-04-28T00:00:00Z
---

## Current Test

number: 3
name: 侧边栏折叠功能
expected: |
  点击头部按钮可以展开/收起侧边栏
awaiting: user response

## Tests

### 1. 后端健康检查端点
expected: 访问 http://localhost:8000/api/v1/health 返回 {"status": "ok"}，前端右上角显示 "Connected"
result: pass

### 2. 前端页面布局
expected: 页面占满整个浏览器窗口，头部、侧边栏、内容区正确显示
result: pass

### 3. 侧边栏折叠功能
expected: 点击头部按钮可以展开/收起侧边栏
result: pending

### 4. 路由导航
expected: 点击导航链接（首页、仪表盘、数据管理、训练任务、模型管理）正确跳转到对应页面
result: pending

### 5. 页面内容正确性
expected: 每个导航页面显示对应的标题（如"数据管理"页面显示"数据管理"标题）
result: pending

### 6. Celery 任务执行
expected: 调用 POST /api/v1/tasks/add 返回任务ID，GET /api/v1/tasks/{id} 可获取计算结果
result: pending

## Summary

total: 6
passed: 2
issues: 0
pending: 4
skipped: 0
blocked: 0

## Gaps

[none yet]
