# UI Top Navigation Redesign

## Problem Background

当前项目采用左侧垂直导航栏布局，与参考网站 vocalremover.org 的顶部水平导航栏设计风格不一致。为了提升用户体验和视觉一致性，需要将布局从 sidebar 模式重构为顶部导航 + 居中内容的模式。

## Goals

1. **布局重构**：将左侧 sidebar 导航改为顶部水平导航栏
2. **内容居中**：所有页面内容采用居中布局，移除 sidebar 偏移
3. **首页优化**：移除上传区域的卡片包装，添加 hero 图片，简化为「选择文件」按钮
4. **配色优化**：对齐参考站点的深色主题配色方案
5. **全局一致性**：分离器、剪辑器、合并器等页面统一采用新的居中布局

## Scope

### Included
- `App.vue` — 侧边栏重构为顶部导航栏
- `HomeView.vue` — 居中布局、hero 图片、简化上传交互
- `FileUploader.vue` — 样式适配
- 全局 CSS 变量 — 配色方案更新
- SplitterView / CutterView / MergerView / BpmKeyView — 适配新布局外壳

### Excluded
- 后端 API 变更
- 新增音频处理功能
- 移动端响应式全面重构（保持现有行为）
- 新增页面或路由

## Non-Goals

- 不改变音频分离/剪辑/合并的核心功能逻辑
- 不引入新的 UI 框架或组件库
- 不重构数据流或状态管理
