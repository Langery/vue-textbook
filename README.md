---
AIGC:
    Label: "1"
    ContentProducer: 001191440300708461136T1XGW3
    ProduceID: a2bf0a7a8afbd1fb49ac51912b613772_0cbb8d8bb0b211f1af37525400826444
    ReservedCode1: lEP910lP3UVlGRIbARJmvlo3VVXv9+nM79i/E+yu9j6RZNlLrhffnomMrI/HQyrV3DJm1FUGK5NuRwk12/WelTmozQI3x3z3w6N8RMS3c5zg12u3XIyamAfXdzuiSIOLff1G4nyHrQkDpy/YDx7+MMuxM/dtHoQdVEjzASxA6U3VzxFihR3tS2WGZPI=
    ContentPropagator: 001191440300708461136T1XGW3
    PropagateID: a2bf0a7a8afbd1fb49ac51912b613772_0cbb8d8bb0b211f1af37525400826444
    ReservedCode2: lEP910lP3UVlGRIbARJmvlo3VVXv9+nM79i/E+yu9j6RZNlLrhffnomMrI/HQyrV3DJm1FUGK5NuRwk12/WelTmozQI3x3z3w6N8RMS3c5zg12u3XIyamAfXdzuiSIOLff1G4nyHrQkDpy/YDx7+MMuxM/dtHoQdVEjzASxA6U3VzxFihR3tS2WGZPI=
---

# Vue 3 入门教材（中文 · 12 章 138 小节）

面向大专/高职计算机专业学生的 Vue 3 中文入门教材，共 12 章 138 小节，附带趣味化讲解、即时练习与章节小结。

## 在线阅读

GitHub Pages 入口（单文件预览版，含折叠导航与完整排版）：

https://langery.github.io/vue-textbook/

## 仓库结构

```
vue-textbook/
├── 教材/            # 00-课程总览.md + 12 个章节目录（01-06、08-13）
├── 配图/            # 章节配图，目录名与教材章节一一对应
├── 工具/            # 构建脚本 md_to_html.py
├── docs/            # GitHub Pages 约定目录：index.html + .nojekyll
└── _dev_artifacts/  # 开发过程产物（历史预览稿等）
```

## 本地使用

- 章节源码为 Markdown，位于 `教材/` 下的 `01-Vue入门与准备` 至 `13-综合项目` 目录（章节编号沿用教材演进历史，第 7 章按编排说明并入第 2 章《模板语法与渲染》，故实际为 12 章，详见 `教材/00-课程总览.md`）。
- 图片位于 `配图/`，构建脚本按文件名自动匹配注入，无需在 Markdown 中写相对路径前缀。
- 重新构建单文件预览：

```bash
python3 工具/md_to_html.py . docs/index.html
```

产物输出到 `docs/index.html`，即 GitHub Pages 入口（仓库 Settings → Pages 中将源设为 `main` 分支的 `/docs` 目录即可，无需额外配置）。

## 构建脚本说明

- `工具/md_to_html.py`：将 `教材/` 下全部 Markdown 章节合并渲染为单文件 HTML，支持折叠式侧边导航、趣味引用样式、打印样式（1280px 断点 + `@media print`）、自然排序。
- 参数：`source`（仓库根目录）、`output`（输出的 HTML 路径）。
*（内容由AI生成，仅供参考）*
