# Brainstorm Summary

- Change: ui-overhaul
- Date: 2026-06-12

## Confirmed Technical Approach

**方案 A：全局 CSS 变量 + 布局重构 + 各 View 局部适配**

- 创建 `styles/variables.css` 定义设计系统（颜色、字体、间距）
- 重构 App.vue 布局：80px 窄侧边栏 + flex:1 宽内容区
- 各 View 页面通过引入变量逐步适配配色和文案
- 只显示已实现的 4 个工具（人声分离、剪辑器、合并器、BPM/调性查询）

## Key Trade-offs and Risks

- 不实现变调器/录音/卡拉OK页面，只保留已实现的工具
- Element Plus 组件库样式可能需要覆盖（如 ElMessage 的配色）
- WaveSurfer.js 波形图的颜色需要适配新配色方案

## Testing Strategy

- 手动验证：每个页面在浏览器中的视觉效果
- 功能回归：确保上传、分离、播放、下载、剪辑、合并、BPM检测功能正常
- 构建验证：`npm run build` 成功

## Spec Patches

None
