# Vue 3 入门教材（中文 · 12 章 123 节）

面向大专/高职计算机专业学生的 Vue 3 中文入门教材，共 12 章 123 小节，附带趣味化讲解、即时练习与章节小结。

## 在线阅读

GitHub Pages 入口（单文件预览版，含折叠导航与完整排版）：

https://langery.github.io/vue-textbook/

## 本地使用

- 各章节源码为 Markdown，位于 `01-Vue入门与准备` 至 `13-综合项目` 目录（章节编号为教材演进历史，实际结构 12 章见 `00-课程总览.md`）。
- 重新构建单文件预览：

```bash
python3 scripts/md_to_html.py
```

产物输出到 `_dev_artifacts/preview.html`；仓库根目录的 `index.html` 为其副本，用作 GitHub Pages 入口。

## 构建脚本说明

- `scripts/md_to_html.py`：将全部 Markdown 章节合并渲染为单文件 HTML，支持折叠式侧边导航、趣味引用样式、打印样式（1280px 断点 + `@media print`）、自然排序。
