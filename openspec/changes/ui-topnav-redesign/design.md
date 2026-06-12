# Design: UI Top Navigation Redesign

## Architecture Decisions

### Layout Model: Sidebar → Top Nav

**Current**: Fixed left sidebar (width defined by `--sidebar-width`) with icon+label vertical navigation, content area offset by sidebar width.

**Target**: Full-width horizontal top navigation bar, content area centered below nav.

```
┌─────────────────────────────────────────────────┐
│  [去人声] [分离器] [剪辑器] [合并器] [BPM] [帮助] │  ← Top Nav
├─────────────────────────────────────────────────┤
│                                                 │
│           ┌───────────────────────┐             │
│           │      Content          │             │  ← Centered
│           │    (max-width: 720px) │             │
│           └───────────────────────┘             │
│                                                 │
└─────────────────────────────────────────────────┘
```

### Component Changes

1. **App.vue** — 替换 sidebar 为顶部 nav bar
   - Nav items: 水平排列，icon + text inline
   - Logo/brand 在最左侧
   - Help 链接在最右侧
   - 固定在页面顶部

2. **HomeView.vue** — 居中布局优化
   - 移除 `upload-card` 包装
   - 保留 hero image placeholder（与 vocalremover.org 的 player image 对应）
   - 上传交互简化为单个「选择文件」按钮
   - 移除独立的「去除人声」提交按钮

3. **FileUploader.vue** — 样式微调
   - 按钮样式对齐参考站点：transparent bg, purple border, border-radius 32px
   - 选中文件后内联显示文件信息

4. **CSS Variables** — 配色更新
   - 参考站点配色：
     - `--mainBgColor: #17171e`
     - `--mainColor: #eee`
     - `--navColor: #1c1c26`
     - `--borderColor: #262633`
     - `--purpleColor: rgb(102, 93, 195)`
   - 保留现有变量名结构，更新色值

5. **其他页面** — 统一居中布局
   - 所有子页面内容区域居中
   - 保持各页面功能 UI 不变（波形编辑器等）

### Approach Selection

采用**渐进式重构**而非一次性重写：
- 优先修改布局外壳（App.vue + CSS variables）
- 然后逐页适配居中布局
- 最后微调组件样式

这样可以保持每个步骤可验证，降低风险。

### Data Flow

无数据流变更。所有改动限于 UI 层（模板结构 + 样式）。
