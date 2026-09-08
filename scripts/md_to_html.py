#!/usr/bin/env python3
"""md_to_html.py — Convert Vue textbook markdown files to a beautiful HTML preview.

Style: 出版级教材 - 加了字号/暗色模式/进度/复制按钮/页码/学习目标高亮
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

try:
    import markdown
except ImportError:
    print("Error: install 'markdown' first: pip install markdown", file=sys.stderr)
    sys.exit(1)


# 13 章主题色 - 按 4 大色系分组
CHAPTER_THEMES = {
    "00": {"bg": "#fff8e7", "accent": "#c92a2a", "label": "课程总览", "icon": "📖"},
    # 入门基础（蓝绿）
    "01": {"bg": "#e7f3ff", "accent": "#1971c2", "label": "Vue 入门", "icon": "🚀"},
    "02": {"bg": "#e7f3ff", "accent": "#1971c2", "label": "模板语法", "icon": "📝"},
    # 组件化（绿色）
    "03": {"bg": "#f0f9e8", "accent": "#2f9e44", "label": "组件化思想", "icon": "🧩"},
    "04": {"bg": "#e7f3ff", "accent": "#1971c2", "label": "Props 与事件", "icon": "📡"},
    # 响应式（橙色）
    "05": {"bg": "#fff4e6", "accent": "#e8590c", "label": "响应式基础", "icon": "⚡"},
    "06": {"bg": "#fff4e6", "accent": "#e8590c", "label": "生命周期", "icon": "🔄"},
    "07": {"bg": "#f0f9e8", "accent": "#2f9e44", "label": "条件列表", "icon": "📋"},
    # 组合式 API（紫色）
    "08": {"bg": "#f3f0ff", "accent": "#7048e8", "label": "组合式 API 精讲", "icon": "🎨"},
    # 路由与状态管理（靛蓝）
    "09": {"bg": "#eef2ff", "accent": "#4338ca", "label": "路由与状态管理", "icon": "🧭"},
    # 服务端通信（青色）
    "10": {"bg": "#e8f4f8", "accent": "#1864ab", "label": "服务端通信", "icon": "🌐"},
    # 表单处理（琥珀）
    "11": {"bg": "#fffbeb", "accent": "#b45309", "label": "表单处理与验证", "icon": "📝"},
    # 测试与调试（玫瑰）
    "12": {"bg": "#fff1f2", "accent": "#be123c", "label": "测试与调试", "icon": "🧪"},
    # 综合项目（暖黄）
    "13": {"bg": "#fff9db", "accent": "#d9480f", "label": "综合项目", "icon": "🏆"},
}


def _natural_key(p: Path):
    """README 排最前，其余按章号.节号自然排序（避免 08.10 < 08.2 的字符串序错误）"""
    name = p.name
    if name == "README.md":
        return (0, 0, name)
    m = re.match(r"(\d+)\.(\d+)", name)
    if m:
        return (int(m.group(1)), int(m.group(2)), name)
    return (99, 99, name)


def collect_chapter_files(source: Path) -> list[dict]:
    chapters: dict[str, dict] = {}

    overview = source / "00-课程总览.md"
    if overview.exists():
        chapters["00"] = {
            "chapter": "00", "files": [overview], "is_overview": True
        }

    for ch_dir in sorted(source.iterdir()):
        if not ch_dir.is_dir():
            continue
        # 跳过公共资源目录（00-公共资源），避免覆盖总览章节 00
        if ch_dir.name.startswith("00-公共资源"):
            continue
        m = re.match(r"^(\d{2})-", ch_dir.name)
        if not m:
            continue
        ch_num = m.group(1)

        files = []
        readme = ch_dir / "README.md"
        if readme.exists():
            files.append(readme)

        for sec_dir in sorted(ch_dir.iterdir(), key=_natural_key):
            if not sec_dir.is_dir():
                continue
            for md_file in sorted(sec_dir.glob("*.md"), key=_natural_key):
                if md_file.name == "README.md":
                    continue
                files.append(md_file)

        ch_title = re.sub(r"^\d{2}-", "", ch_dir.name)
        chapters[ch_num] = {
            "chapter": ch_num,
            "title": ch_title,
            "files": files,
            "is_overview": False,
        }

    return [chapters[k] for k in sorted(chapters.keys()) if chapters[k]["files"]]


def build_image_map(source: Path) -> dict[str, str]:
    """Scan 00-公共资源/图/ for actual image files.

    Returns {key: relative_path} where key is both the basename
    (e.g. "图1-3.png") and the stem (e.g. "图1-3") for fuzzy matching.
    """
    img_root = source / "00-公共资源" / "图"
    if not img_root.is_dir():
        return {}

    img_map: dict[str, str] = {}
    for f in img_root.rglob("*"):
        if f.suffix.lower() in (".png", ".svg", ".jpg", ".jpeg", ".gif", ".webp"):
            rel = f.resolve().as_posix()  # absolute path for file:// usage
            img_map[f.name] = rel
            img_map[f.stem] = rel  # stem for extension-agnostic lookup
    return img_map


MISSING_IMG_SVG = (
    '<span class="missing-img">'
    '<svg xmlns="http://www.w3.org/2000/svg" width="360" height="48"'
    ' viewBox="0 0 360 48" preserveAspectRatio="xMidYMid meet">'
    '<rect width="360" height="48" fill="#f8f9fa" rx="4" stroke="#dee2e6" stroke-width="1"/>'
    '<text x="180" y="29" text-anchor="middle" fill="#868e96" font-family="sans-serif" font-size="13">'
    '（图片暂缺：{label}）</text></svg></span>')


def _get_image_dimensions(raw: bytes, ext: str):
    """Return (width, height) of image bytes using only stdlib, or None."""
    import struct
    try:
        if ext == ".png" and raw[:8] == b"\x89PNG\r\n\x1a\n":
            w, h = struct.unpack(">II", raw[16:24])
            return w, h
        if ext == ".gif" and raw[:6] in (b"GIF87a", b"GIF89a"):
            w, h = struct.unpack("<HH", raw[6:10])
            return w, h
        if ext in (".jpg", ".jpeg") and raw[:2] == b"\xff\xd8":
            i = 2
            while i + 9 < len(raw):
                if raw[i] != 0xFF:
                    i += 1
                    continue
                marker = raw[i + 1]
                if marker in (0xD8, 0xD9) or 0xD0 <= marker <= 0xD7:
                    i += 2
                    continue
                seg_len = struct.unpack(">H", raw[i + 2:i + 4])[0]
                if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7,
                              0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                    h, w = struct.unpack(">HH", raw[i + 5:i + 9])
                    return w, h
                i += 2 + seg_len
            return None
        if ext == ".webp" and raw[:4] == b"RIFF" and raw[8:12] == b"WEBP":
            fmt = raw[12:16]
            if fmt == b"VP8X" and len(raw) >= 30:
                w = raw[24] | (raw[25] << 8) | (raw[26] << 16)
                h = raw[27] | (raw[28] << 8) | (raw[29] << 16)
                return w + 1, h + 1
            if fmt == b"VP8 " and len(raw) >= 30:
                w, h = struct.unpack("<HH", raw[26:30])
                return w & 0x3FFF, h & 0x3FFF
            if fmt == b"VP8L" and len(raw) >= 25:
                bits = struct.unpack("<I", raw[21:25])[0]
                return (bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1
            return None
        if ext == ".svg":
            text = raw.decode("utf-8", errors="ignore")
            mw = re.search(r'<svg[^>]*\bwidth=["\']([\d.]+)["\']', text)
            mh = re.search(r'<svg[^>]*\bheight=["\']([\d.]+)["\']', text)
            if mw and mh:
                return int(float(mw.group(1))), int(float(mh.group(1)))
            vb = re.search(
                r'viewBox=["\']\s*[\d.-]+\s+[\d.-]+\s+([\d.]+)\s+([\d.]+)\s*["\']',
                text)
            if vb:
                return max(1, int(float(vb.group(1)))), max(1, int(float(vb.group(2))))
    except Exception:
        return None
    return None


def rewrite_image_src(html: str, img_map: dict[str, str]) -> str:
    """Rewrite <img src> to embedded data URIs (base64).

    Using data URIs avoids the file:// cross-origin restriction that
    prevents SVG/PNG from loading in <img> tags on file:// pages.
    """
    import base64

    def _replace(m: re.Match) -> str:
        tag = m.group(0)
        src = m.group(1)
        alt = m.group(2) or ""

        basename = Path(src).name
        stem = Path(src).stem

        # resolve actual file path
        real_path = None
        if basename in img_map:
            real_path = img_map[basename]
        elif stem in img_map:
            real_path = img_map[stem]

        if real_path is None:
            # missing — placeholder
            label = alt or basename
            placeholder = MISSING_IMG_SVG.replace("{label}", label)
            return placeholder

        # embed as base64 data URI
        ext = Path(real_path).suffix.lower()
        mime_map = {
            ".svg":  "image/svg+xml",
            ".png":  "image/png",
            ".jpg":  "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif":  "image/gif",
            ".webp": "image/webp",
        }
        mime = mime_map.get(ext, "application/octet-stream")

        if ext == ".svg":
            # minify SVG: strip redundant whitespace between tags
            raw_text = Path(real_path).read_text(encoding="utf-8")
            raw_text = re.sub(r">\s+<", "><", raw_text)
            raw_text = re.sub(r"\n\s*", "", raw_text)
            raw = raw_text.encode("utf-8")
        else:
            raw = Path(real_path).read_bytes()

        b64 = base64.b64encode(raw).decode("ascii")
        data_uri = f"data:{mime};base64,{b64}"

        # add loading="lazy" for off-screen images
        if 'loading=' not in tag:
            tag = tag.replace("<img ", '<img loading="lazy" ', 1)

        # reserve layout space so lazy images don't shift anchor targets
        if 'width=' not in tag and 'height=' not in tag:
            dims = _get_image_dimensions(raw, ext)
            if dims:
                w, h = dims
                tag = tag.replace("<img ", f'<img width="{w}" height="{h}" ', 1)

        return tag.replace(src, data_uri)

    return re.sub(
        r'<img\s[^>]*src="([^"]+)"[^>]*(?:alt="([^"]*)")?[^>]*/?>',
        _replace,
        html,
    )


def md_to_html(text: str) -> str:
    """Convert markdown to HTML body fragment."""
    # 清理连续的空 fenced code 块（防止 wrap_mindmaps 错误留下的双重 ```）
    text = re.sub(r'```\s*\n```text', '```text', text)
    # 思维导图识别：用户用 ```text 围栏 + ASCII 树状结构
    # （不需要特殊标记，普通代码块即可，CSS 识别 text 类的树状结构）
    md = markdown.Markdown(
        extensions=["extra", "sane_lists", "smarty", "fenced_code"],
        output_format="html5",
    )
    html = md.convert(text)
    html = _escape_script_tags_outside_pre(html)
    # 学习目标标题加 class（卡片样式）
    html = re.sub(r'<h2>(.*?学习目标.*?)</h2>', r'<h2 class="h2-goals">\1</h2>', html)
    # 表格包横向滚动容器，防窄屏裁切
    html = re.sub(r'(<table[^>]*>)', r'<div class="table-wrap">\1', html)
    html = html.replace('</table>', '</table></div>')
    html = _classify_fun_quotes(html)
    return html


# 趣味引用块分类：按首段首个 emoji 给 blockquote 加类型 class，并把 emoji 提为头像 span
# 💬/🧑/🤖/👨🏫/🙋 → 对话气泡；💡 → 小贴士；⚠️ → 踩坑警告；📌 → 记忆点；🔍 → 深挖
_FUN_QUOTE_RE = re.compile(r'<blockquote>\s*<p>([🧑🤖👨🏫🙋🐱💬💡⚠️📌🔍])')

def _classify_fun_quotes(html: str) -> str:
    type_map = {
        '💬': 'chat', '🧑': 'chat', '🤖': 'chat', '👨🏫': 'chat', '🙋': 'chat', '🐱': 'chat',
        '💡': 'tip', '⚠️': 'warn', '📌': 'note', '🔍': 'deep',
    }
    def _repl(m: re.Match) -> str:
        emoji = m.group(1)
        cls = type_map.get(emoji, 'chat')
        return f'<blockquote class="quote-{cls}">\n<p><span class="q-avatar">{emoji}</span>'
    return _FUN_QUOTE_RE.sub(_repl, html)


def _escape_script_tags_outside_pre(html: str) -> str:
    """Escape <script>/</script>/<style>/</style> tags not inside <pre> blocks.

    When markdown fenced code blocks are malformed, the markdown parser may
    output raw <script> tags that get interpreted by the browser, breaking
    page rendering. This postprocessor ensures they're always safe.
    """
    result = []
    last_end = 0
    # Find all <pre>...</pre> blocks and protect their content
    for m in re.finditer(r'<pre>.*?</pre>', html, re.DOTALL):
        # Escape script/style tags in text OUTSIDE <pre> blocks
        before = html[last_end:m.start()]
        before = before.replace('<script', '&lt;script')
        before = before.replace('</script', '&lt;/script')
        before = before.replace('<style', '&lt;style')
        before = before.replace('</style', '&lt;/style')
        result.append(before)
        result.append(m.group(0))
        last_end = m.end()
    # Escape remaining text after last <pre>
    tail = html[last_end:]
    tail = tail.replace('<script', '&lt;script')
    tail = tail.replace('</script', '&lt;/script')
    tail = tail.replace('<style', '&lt;style')
    tail = tail.replace('</style', '&lt;/style')
    result.append(tail)
    return ''.join(result)


def add_code_copy_buttons(html: str) -> str:
    """为每个 <pre>...</pre> 单独包一层 div（不能合并所有）。

    特殊处理：如果 pre 内容是 'text' 类的思维导图（用 :::mindmap 标记转换的），
    给 .code-block 加 .mindmap 类，用浅色背景而非深色。
    """
    parts = []
    last_end = 0
    for m in re.finditer(r'<pre>.*?</pre>', html, flags=re.DOTALL):
        parts.append(html[last_end:m.start()])
        lang_match = re.search(r'class="language-(\w+)"', m.group(0))
        lang = lang_match.group(1) if lang_match else "text"

        # 特殊处理：text 类的思维导图（用浅色 + 等宽字体，但更友好）
        is_mindmap = (lang == 'text' and '├──' in m.group(0))

        block_class = "code-block mindmap-block" if is_mindmap else "code-block"

        parts.append(
            f'<div class="{block_class}">'
            f'<div class="code-header">'
            f'<span class="code-lang">{lang}</span>'
            f'<button class="code-copy" onclick="copyCode(this)">复制</button>'
            f'</div>'
            f'{m.group(0)}'
            f'</div>'
        )
        last_end = m.end()
    parts.append(html[last_end:])
    return "".join(parts)


def extract_h2_titles_from_html(html: str) -> list[str]:
    """从渲染后的 HTML 提取 h2 标题（去标签，用于三级导航）。

    注意：必须从渲染后的 HTML 提取，而不是 md 原文的 `## ` 行——
    部分源文件存在未闭合代码块，markdown 解析会把后续 `## ` 吞进代码块，
    若按原文提取会导致导航锚点与正文锚点错位。
    """
    titles = []
    for m in re.finditer(r"<h2[^>]*>(.*?)</h2>", html, flags=re.DOTALL):
        t = re.sub(r"<[^>]+>", "", m.group(1))
        t = t.strip()
        if t:
            titles.append(t)
    return titles


def render_section_html(text: str) -> str:
    """将 md 小节正文渲染为 HTML（去掉首个 h1，供正文与导航共用）。"""
    text = re.sub(r"^#\s+.+?\n", "", text, count=1, flags=re.MULTILINE)
    return md_to_html(text)


def make_nav(chapters: list[dict]) -> str:
    items = []
    for ch in chapters:
        theme = CHAPTER_THEMES.get(ch["chapter"], {"accent": "#666", "label": ch.get("title", ""), "icon": "📄"})

        if ch.get("is_overview"):
            items.append(
                f'<li><a href="#ch-{ch["chapter"]}" class="nav-overview">'
                f'<span class="nav-icon">{theme["icon"]}</span> {theme["label"]}</a></li>'
            )
        else:
            sub_items = []
            for f in ch["files"]:
                fid = f.stem
                anchor = f"sec-{ch['chapter']}-{fid}"
                title = re.sub(r"^\d+\.\d+-", "", fid)
                if fid == "README":
                    title = "章引言"
                # 三级导航：小节内 h2（从渲染后 HTML 提取，与正文锚点一致）
                try:
                    body_html = render_section_html(f.read_text(encoding="utf-8"))
                    h2_titles = extract_h2_titles_from_html(body_html)
                except Exception:
                    h2_titles = []
                sub3_items = ""
                if h2_titles:
                    sub3 = "".join(
                        f'<li><a href="#{anchor}-h2-{i}" class="nav-subsub">{t}</a></li>'
                        for i, t in enumerate(h2_titles, 1)
                    )
                    sub3_items = f'<ul class="nav-subsub-list">{sub3}</ul>'
                sub_cls = "nav-sub-item has-sub" if h2_titles else "nav-sub-item"
                sub_caret = '<span class="nav-caret-sub" aria-hidden="true">▸</span>' if h2_titles else ""
                sub_items.append(
                    f'<li class="{sub_cls}">'
                    f'<a href="#{anchor}" class="nav-sub">{sub_caret}{title}</a>'
                    f'{sub3_items}'
                    f'</li>'
                )
            items.append(
                f'<li class="nav-chapter">'
                f'<a href="#ch-{ch["chapter"]}" class="nav-chapter-title" '
                f'style="--nav-accent: {theme["accent"]};">'
                f'<span class="nav-caret" aria-hidden="true">▸</span>'
                f'<span class="nav-icon">{theme["icon"]}</span>'
                f'第 {int(ch["chapter"])} 章 {theme["label"]}</a>'
                f'<ul class="nav-subsection">{"".join(sub_items)}</ul>'
                f'</li>'
            )
    return "<ul class='nav-list'>" + "".join(items) + "</ul>"


def add_h2_anchors(html: str, anchor: str) -> str:
    """给小节正文的 h2 添加 id 锚点（sec-xx-小节-h2-N）。"""
    counter = [0]

    def _repl(m):
        counter[0] += 1
        attrs = m.group(1)
        if 'id=' in attrs:
            return m.group(0)
        return f'<h2 id="{anchor}-h2-{counter[0]}"{attrs}>'

    return re.sub(r"<h2([^>]*)>", _repl, html)


def make_chapter_html(ch: dict) -> str:
    if not ch["files"]:
        return ""

    theme = CHAPTER_THEMES.get(ch["chapter"], {"bg": "#fdfaf2", "accent": "#666", "icon": "📄", "label": ch.get("title", "")})
    if ch.get("is_overview"):
        text = ch["files"][0].read_text(encoding="utf-8")
        body = add_code_copy_buttons(md_to_html(text))
        return (
            f'<section id="ch-00" class="chapter" style="--ch-bg: {theme["bg"]}; --ch-accent: {theme["accent"]};">'
            f'<div class="chapter-cover">'
            f'<div class="chapter-header">'
            f'<span class="chapter-icon">{theme["icon"]}</span>'
            f'<div class="chapter-header-text">'
            f'<div class="chapter-num-label">课程总览</div>'
            f'<h1 class="chapter-title">{theme["label"]}</h1>'
            f'<div class="chapter-meta">📚 全书导览 · 12 章 / 123 节 · 64 课时</div>'
            f'</div>'
            f'</div>'
            f'</div>'
            f'<div class="chapter-body">{body}</div>'
            f'</section>'
        )

    # 正常章 - 封面 + 正文分两块
    sections = []
    for idx, f in enumerate(ch["files"], 1):
        text = f.read_text(encoding="utf-8")
        anchor = f"sec-{ch['chapter']}-{f.stem}"
        section_num = f"{int(ch['chapter'])}.{idx - 1}" if idx > 1 else f"{int(ch['chapter'])}"

        if f.name == "README.md":
            h1_match = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
            if h1_match:
                text = re.sub(r"^#\s+.+?\n", "", text, count=1, flags=re.MULTILINE)
                title = h1_match.group(1).strip()
                section_num_label = "📋"
                body = add_code_copy_buttons(md_to_html(text))
                body = add_h2_anchors(body, anchor)
                sections.append(
                    f'<article id="{anchor}" class="section section-intro">'
                    f'<h2 class="section-title"><span class="section-num">{section_num_label}</span>{title}</h2>'
                    f'<div class="section-body">{body}</div>'
                    f'</article>'
                )
                continue

        # strip the first h1 line from .md text so section-body starts from h2
        h1_match = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
        if h1_match:
            text = re.sub(r"^#\s+.+?\n", "", text, count=1, flags=re.MULTILINE)
            title = h1_match.group(1).strip()
            # remove leading number prefix like "1.1 " for display
            title = re.sub(r"^\d+\.\d+\s+", "", title)
        else:
            title = re.sub(r"^\d+\.\d+-", "", f.stem)

        body = add_code_copy_buttons(md_to_html(text))
        body = add_h2_anchors(body, anchor)
        sections.append(
            f'<article id="{anchor}" class="section">'
            f'<h2 class="section-title"><span class="section-num">{section_num}</span>{title}</h2>'
            f'<div class="section-body">{body}</div>'
            f'</article>'
        )

    return (
        f'<section id="ch-{ch["chapter"]}" class="chapter" style="--ch-bg: {theme["bg"]}; --ch-accent: {theme["accent"]};">'
        f'<div class="chapter-cover">'
        f'<div class="chapter-header">'
        f'<span class="chapter-icon">{theme["icon"]}</span>'
        f'<div class="chapter-header-text">'
        f'<div class="chapter-num-label">第 {int(ch["chapter"])} 章</div>'
        f'<h1 class="chapter-title">{theme["label"]}</h1>'
        f'<div class="chapter-meta">📚 {len(ch["files"])} 个小节 · ⏱ 预计 2-3 小时</div>'
        f'</div>'
        f'</div>'
        f'</div>'
        f'<div class="chapter-body">{"".join(sections)}</div>'
        f'</section>'
    )


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN" data-theme="light">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} - 预览</title>
<style>
  /* ===== 基础 ===== */
  *, *::before, *::after { margin: 0; padding: 0; box-sizing: border-box; }
  html { font-size: 16px; -webkit-text-size-adjust: 100%; scroll-behavior: smooth; }

  /* ===== 主题色变量（亮/暗双主题） ===== */
  :root, [data-theme="light"] {
    --bg: #fdfaf2;
    --bg-card: #ffffff;
    --bg-code: #f7f3eb;
    --bg-quote: #faf6ed;
    --text: #2c2c2c;
    --text-soft: #5c5c5c;
    --text-faint: #8a8a8a;
    --border: #e8e0d0;
    --border-soft: #f0e8d8;
    --topbar-bg: linear-gradient(135deg, #2c3e50 0%, #42b883 100%);
    --shadow: 0 2px 8px rgba(0,0,0,0.05);
  }
  [data-theme="dark"] {
    --bg: #1a1d23;
    --bg-card: #252932;
    --bg-code: #1e2128;
    --bg-quote: #2a2d35;
    --text: #e8e6e3;
    --text-soft: #a8a6a3;
    --text-faint: #6a6a6a;
    --border: #3a3d45;
    --border-soft: #2a2d35;
    --topbar-bg: linear-gradient(135deg, #1a1d23 0%, #2d4a3e 100%);
    --shadow: 0 2px 8px rgba(0,0,0,0.3);
  }

  /* ===== 全局 ===== */
  body {
    background: var(--bg);
    color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Hiragino Sans GB",
                 "Microsoft YaHei", "Helvetica Neue", Arial, sans-serif;
    line-height: 1.85;
    -webkit-font-smoothing: antialiased;
    transition: background 0.2s, color 0.2s;
  }

  /* ===== 字号（可调） ===== */
  body.font-small { font-size: 14px; }
  body.font-normal { font-size: 16px; }
  body.font-large { font-size: 18px; }

  /* ===== 顶栏 ===== */
  .topbar {{
    background: rgba(255, 255, 255, 0.85);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    color: #1e1e1e;
    padding: 12px 40px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06), 0 4px 12px rgba(0,0,0,0.04);
    border-bottom: 1px solid var(--border-soft);
    position: sticky; top: 0; z-index: 100;
    display: flex; align-items: center; justify-content: space-between;
  }}
  [data-theme="dark"] .topbar {{ background: rgba(26, 29, 35, 0.85); color: #e8e6e3; }}
  .topbar h1 {{ font-size: 17px; font-weight: 700; letter-spacing: 0.3px; }}
  .topbar h1 .book-icon {{ color: #42b883; margin-right: 6px; }}
  .topbar .meta {{ font-size: 12px; color: var(--text-soft); margin-right: 12px; }}
  .topbar-tools {{ display: flex; gap: 4px; align-items: center; }}
  .tool-btn {{
    background: transparent;
    color: var(--text-soft);
    border: 1px solid var(--border);
    padding: 5px 10px;
    border-radius: 6px;
    cursor: pointer;
    font-size: 12px;
    font-family: inherit;
    transition: all 0.15s;
  }}
  .tool-btn:hover {{ background: var(--bg-quote); color: var(--text); border-color: var(--text-soft); }}
  .tool-btn.active {{ background: var(--ch-accent, #1971c2); color: white; border-color: var(--ch-accent, #1971c2); font-weight: 600; }}

  /* ===== 主体布局 ===== */
  .layout { display: flex; max-width: 1680px; margin: 0 auto; }

  /* ===== 左侧导航 ===== */
  .sidebar {
    width: 260px;
    flex-shrink: 0;
    padding: 24px 14px 18px;
    height: calc(100vh - 52px);
    overflow-y: auto;
    overscroll-behavior: contain; /* 全部展开后滚动列表不把滚动穿透到页面 */
    scrollbar-gutter: stable;
    position: sticky; top: 52px;
    border-right: 1px solid var(--border);
    background: var(--bg-card);
  }
  .nav-list { list-style: none; padding-bottom: 34px; }
  .nav-list > li { margin-bottom: 4px; }
  .nav-chapter-title {
    display: flex; align-items: center; gap: 8px;
    padding: 9px 11px;
    margin: 12px 0 4px;
    font-size: 14px;
    font-weight: 700;
    color: var(--text);
    text-decoration: none;
    border-left: 3px solid var(--nav-accent, #1e1e1e);
    background: var(--bg-quote);
    border-radius: 0 4px 4px 0;
    transition: all 0.15s;
  }
  .nav-chapter-title:hover { background: var(--bg-code); transform: translateX(2px); }
  .nav-chapter-title.nav-active {
    background: var(--nav-accent, #1e1e1e);
    color: white;
    box-shadow: 0 2px 6px rgba(0,0,0,0.1);
  }
  .nav-subsection { list-style: none; margin-left: 0; padding-left: 18px; border-left: 1px dashed var(--border); margin: 4px 0 4px 18px; }
  .nav-subsection li { margin: 1px 0; }
  .nav-sub {
    display: block;
    padding: 4px 10px;
    font-size: 12.5px;
    color: var(--text-soft);
    text-decoration: none;
    border-radius: 3px;
    transition: all 0.12s;
    line-height: 1.4;
  }
  .nav-sub:hover { color: var(--nav-accent, #1971c2); background: var(--bg-quote); }
  .nav-subsub-list {
    list-style: none;
    margin: 1px 0 4px;
    padding-left: 12px;
    border-left: 1px dotted var(--border);
    margin-left: 14px;
  }
  .nav-subsub-list li { margin: 1px 0; }
  .nav-subsub {
    display: block;
    padding: 2px 8px;
    font-size: 11.5px;
    color: var(--text-soft);
    text-decoration: none;
    border-radius: 3px;
    transition: all 0.12s;
    line-height: 1.35;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    max-width: 210px;
  }
  [data-theme="dark"] .nav-subsub { color: #b8b6b3; }
  .nav-subsub:hover { color: var(--nav-accent, #1971c2); background: var(--bg-quote); }
  .nav-overview {
    display: flex; align-items: center; gap: 8px;
    padding: 9px 11px;
    color: #c92a2a;
    font-weight: 600;
    text-decoration: none;
    border-left: 3px solid #c92a2a;
    background: #fff5f5;
    border-radius: 0 4px 4px 0;
  }
  [data-theme="dark"] .nav-overview { background: #3a2828; }
  .nav-icon { font-size: 14px; }

  /* ===== 折叠式导航 ===== */
  .nav-caret {
    display: inline-flex; align-items: center; justify-content: center;
    width: 14px; height: 14px; flex-shrink: 0;
    font-size: 11px; line-height: 1;
    margin-top: -1px; /* 光学微调：抵消 ▸ 字形在 14px 盒内偏下的 1px 渲染偏移 */
    color: var(--text-faint, #999);
    transition: transform 0.18s ease, color 0.15s;
  }
  .nav-chapter > .nav-subsection { display: none; }
  .nav-chapter.open > .nav-subsection { display: block; }
  .nav-chapter.open > .nav-chapter-title .nav-caret {
    transform: rotate(90deg);
    color: var(--nav-accent, #1971c2);
  }
  .nav-chapter.open > .nav-chapter-title { background: var(--bg-code); }
  /* 当前章展开时保持高亮深底白字：避免 .open 的浅色背景覆盖 .nav-active 造成白字浅底、对比度不足 */
  .nav-chapter.open > .nav-chapter-title.nav-active {
    background: var(--nav-accent, #1e1e1e);
    color: #fff;
    box-shadow: 0 2px 6px rgba(0,0,0,0.12);
  }
  [data-theme="dark"] .nav-chapter.open > .nav-chapter-title.nav-active {
    color: #fff;
  }
  .nav-caret-sub {
    display: inline-block;
    width: 11px;
    margin-right: 2px;
    font-size: 10px;
    line-height: 1;
    vertical-align: -1px; /* 行内基线微调：让 ▸ 与中文标题视觉中心对齐 */
    color: var(--text-faint, #999);
    transition: transform 0.18s ease, color 0.15s;
  }
  .nav-sub-item > .nav-subsub-list { display: none; }
  .nav-sub-item.open > .nav-subsub-list { display: block; }
  .nav-sub-item.open > .nav-sub .nav-caret-sub {
    transform: rotate(90deg);
    color: var(--nav-accent, #1971c2);
  }
  .nav-sub-item.open > .nav-sub { color: var(--text); font-weight: 600; }
  /* 展开动画：轻微下落 + 淡入，柔化展开手感；收起依赖 display:none 折叠主逻辑，不做反向过渡以免破坏既有交互 */
  @keyframes navDropIn {
    from { opacity: 0; transform: translateY(-5px); }
    to { opacity: 1; transform: translateY(0); }
  }
  .nav-chapter.open > .nav-subsection,
  .nav-sub-item.open > .nav-subsub-list {
    animation: navDropIn 0.22s cubic-bezier(0.2, 0.7, 0.3, 1);
    transform-origin: top;
  }
  @media (prefers-reduced-motion: reduce) {
    .nav-chapter.open > .nav-subsection,
    .nav-sub-item.open > .nav-subsub-list { animation: none; }
  }
  .nav-toolbar {
    display: flex; gap: 6px;
    margin-bottom: 8px;
    padding: 6px 2px 2px;
    position: sticky; top: 0; z-index: 5;
    background: var(--bg-card);
  }
  .nav-tool-btn {
    flex: 1;
    padding: 5px 0;
    font-size: 12px;
    color: var(--text-soft);
    background: transparent;
    border: 1px solid var(--border);
    border-radius: 6px;
    cursor: pointer;
    font-family: inherit;
    transition: all 0.15s;
  }
  .nav-tool-btn:hover { color: var(--text); background: var(--bg-quote); border-color: var(--text-soft); }

  /* ===== 右侧内容 ===== */
  .content {{
    flex: 1;
    padding: 36px 44px 80px;
    min-width: 0;
  }}

  /* ===== 章 ===== */
  .chapter {{
    --ch-bg: #fdfaf2;
    --ch-accent: #1e1e1e;
    background: #ffffff;
    border: 1px solid #e8e0d0;
    border-radius: 14px;
    padding: 0;
    margin-bottom: 36px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.08), 0 8px 24px rgba(0,0,0,0.10);
    position: relative;
    max-width: 1200px;
    margin-left: auto;
    margin-right: auto;
    border-left: 4px solid var(--ch-accent);
    overflow: hidden;
  }}
  /* 章节封面 - 渐变背景（跟随各章主题色，暗色模式深色化） */
  .chapter-cover {{
    background: linear-gradient(135deg, var(--ch-bg, #e7f3ff) 0%, #ffffff 100%);
    padding: 36px 48px 32px;
    border-bottom: 1px solid #e8e0d0;
  }}
  [data-theme="dark"] .chapter-cover {{
    background: linear-gradient(135deg, rgba(255,255,255,0.07), rgba(255,255,255,0.02));
    border-bottom-color: var(--border);
  }}
  .chapter-body {{ padding: 6px 48px 44px; }}
  [data-theme="dark"] .chapter { background: var(--bg-card); }
  .chapter-header {
    display: flex; align-items: center; gap: 18px;
    padding-bottom: 18px; margin-bottom: 24px;
    border-bottom: 2px solid var(--ch-accent);
  }
  .chapter-icon {
    font-size: 40px;
    line-height: 1;
    flex-shrink: 0;
  }
  .chapter-header-text {{ flex: 1; }}
  .chapter-num-label {{
    display: inline-block;
    font-size: 11px;
    font-weight: 700;
    color: white;
    background: var(--ch-accent);
    padding: 3px 12px;
    border-radius: 3px;
    letter-spacing: 2px;
    margin-bottom: 10px;
  }}
  .chapter-title {{
    font-size: 32px;
    font-weight: 800;
    color: var(--ch-accent);
    line-height: 1.15;
    margin: 0;
    letter-spacing: -0.01em;
  }}
  .chapter-meta {
    font-size: 12px;
    color: var(--text-soft);
    margin-top: 6px;
    opacity: 0.85;
  }
  .chapter-footer {
    margin-top: 28px;
    padding-top: 16px;
    border-top: 1px dashed var(--border);
    text-align: center;
    font-size: 12px;
    color: var(--text-faint);
  }

  /* ===== 小节 ===== */
  .section {
    margin-bottom: 48px;
    padding: 0;
  }
  /* 章引言特殊样式 */
  .section-intro {
    background: none;
    border: none;
  }
  .section-intro .section-num {
    background: none;
    color: var(--ch-accent);
    border: none;
    font-size: inherit;
    margin-right: 6px;
  }
  .section-num {
    display: inline;
    margin-right: 6px;
    color: var(--ch-accent);
    font-size: 0.875em;
    font-weight: 700;
  }
  .section-title {
    font-size: 1.06em;
    font-weight: 600;
    color: var(--text);
    margin-bottom: 16px;
    padding-bottom: 0;
    border-bottom: none;
  }


  /* ===== 排版 ===== */
  .chapter-body p, .section-body p {
    margin: 12px 0;
    color: var(--text);
    line-height: 1.82;
    /* 行宽由 .chapter + .chapter-body 内边距统一约束（约 68 中文字），块级自动撑满 */
    max-width: none;
  }
  .chapter-body strong, .section-body strong { color: #c92a2a; font-weight: 600; }
  [data-theme="dark"] .chapter-body strong, [data-theme="dark"] .section-body strong { color: #ff6b6b; }
  .chapter-body em, .section-body em { color: var(--text-soft); font-style: italic; }
  .chapter-body a, .section-body a {
    color: var(--ch-accent);
    text-decoration: none;
    border-bottom: 1px dotted;
  }
  .chapter-body a:hover, .section-body a:hover { border-bottom-style: solid; }
  .chapter-body a[href^="http"]::after, .section-body a[href^="http"]::after {
    content: " ↗";
    font-size: 0.85em;
    opacity: 0.6;
  }

  /* ===== 标题层级（节 > 小节 > 三级 > 四级） ===== */
  /* 章内一级标题（README 引言等） */
  /* 标题层级间距：自上而下按 1.6~1.8× 字号节奏递减，前后节奏统一 */
  .chapter-body h1, .section-body h1 {{
    font-size: 1.25em; font-weight: 700;
    color: var(--ch-accent);
    margin: 34px 0 16px;
    line-height: 1.4;
    letter-spacing: -0.01em;
  }}

  /* H2（小节标题） */
  .chapter-body h2, .section-body h2 {{
    font-size: 1.19em; font-weight: 700;
    color: var(--text);
    margin: 36px 0 14px;
    padding: 0 0 10px;
    border-bottom: 1px solid var(--border-soft);
    line-height: 1.45;
  }}
  .chapter-body h2:first-of-type, .section-body h2:first-of-type {{
    margin-top: 10px;
  }}

  /* H3 */
  .chapter-body h3, .section-body h3 {{
    font-size: 1.06em; font-weight: 650;
    color: var(--text);
    margin: 26px 0 10px;
    line-height: 1.45;
  }}

  /* H4 */
  .chapter-body h4, .section-body h4 {{
    font-size: 0.94em; font-weight: 600;
    color: var(--text-soft);
    margin: 20px 0 8px;
    line-height: 1.5;
  }}

  /* ===== 学习目标卡片（🎯） ===== */
  .h2-goals {{
    background: linear-gradient(90deg, var(--ch-bg, #fff8e7), transparent);
    border-left: 4px solid #e8a33d;
    padding: 10px 14px;
    border-radius: 0 8px 8px 0;
  }}
  .h2-goals + p + ul, .h2-goals + ul {{
    background: var(--bg-quote);
    border: 1px solid var(--border-soft);
    border-radius: 10px;
    padding: 14px 20px 14px 34px;
    margin: 12px 0 20px;
  }}
  [data-theme="dark"] .h2-goals {{ background: linear-gradient(90deg, rgba(255,255,255,0.06), transparent); }}

  /* ===== 纯 CSS 树形思维导图 ===== */
  .markmap {{
    background: #fffdf8;
    border: 1px solid #e8e0d0;
    border-radius: 12px;
    padding: 22px 24px;
    margin: 24px 0;
    max-width: none;
  }}
  .markmap ul, .markmap ol {{ list-style: none; padding: 0; margin: 0; }}
  .markmap li {{
    position: relative;
    padding: 3px 0;
    line-height: 1.65;
    transition: color 0.2s;
  }}
  .markmap li::before {{
    content: '';
    position: absolute;
    left: -14px;
    top: 10px;
    width: 4px;
    height: 4px;
    border-radius: 50%;
    transition: background 0.2s;
  }}
  /* 一级节点 */
  .markmap > ul > li {{
    font-size: 15px; font-weight: 600;
    color: #4a3720;
    padding-left: 18px;
    margin-top: 6px;
  }}
  .markmap > ul > li::before {{ left: 0; top: 11px; background: #b8956a; }}
  .markmap > ul > li:first-child {{ margin-top: 0; }}
  /* 二级节点 */
  .markmap > ul > li > ul > li {{
    font-size: 14px;
    color: #5c4a2e;
    padding-left: 12px;
  }}
  .markmap > ul > li > ul > li::before {{ left: -12px; background: #c9ad7e; }}
  /* 三级节点 */
  .markmap > ul > li > ul > li > ul > li {{
    font-size: 13px;
    color: #7a6a55;
    padding-left: 24px;
  }}
  .markmap > ul > li > ul > li > ul > li::before {{ left: -12px; background: #d4c5a0; }}
  /* hover */
  .markmap li:hover {{ background: rgba(0,0,0,0.03); border-radius: 4px; }}
  .markmap li:hover::before {{ background: #8b6f3f; transform: scale(1.3); }}
  .markmap > h1, .markmap > h2, .markmap > h3 {{
    font-size: 16px; font-weight: 700;
    color: #4a3720;
    margin: 0 0 10px -4px;
    line-height: 1.5;
  }}
  /* 学习路径横向步骤条 */
  .learning-path {{
    display: flex; align-items: center; flex-wrap: wrap;
    gap: 6px;
    margin-top: 16px;
    padding-top: 14px;
    border-top: 1px dashed #e0d5c0;
  }}
  .learning-path .step {{
    background: #f0e8d8;
    color: #5c4a2e;
    padding: 4px 12px;
    border-radius: 14px;
    font-size: 13px;
    font-weight: 600;
    white-space: nowrap;
  }}
  .learning-path .arrow {{
    color: #b8956a;
    font-size: 14px;
    margin: 0 2px;
  }}
  /* dark */
  [data-theme="dark"] .markmap {{ background: #1e1e1e; border-color: #333; }}
  [data-theme="dark"] .markmap > ul > li {{ color: #d4c5a0; }}
  [data-theme="dark"] .markmap > ul > li > ul > li {{ color: #b8b8b8; }}
  [data-theme="dark"] .markmap > ul > li > ul > li > ul > li {{ color: #888; }}
  [data-theme="dark"] .markmap li:hover {{ background: rgba(255,255,255,0.05); border-radius: 4px; color: #eee; }}
  [data-theme="dark"] .markmap > h1, [data-theme="dark"] .markmap > h2, [data-theme="dark"] .markmap > h3 {{ color: #d4c5a0; }}
  [data-theme="dark"] .learning-path {{ border-top-color: #333; }}
  [data-theme="dark"] .learning-path .step {{ background: #2a2a2a; color: #c8c8c8; }}
  [data-theme="dark"] .learning-path .arrow {{ color: #8b6f3f; }}

  /* 学习目标 🎯 */
  .section-body > p:first-of-type:has(strong:contains("学习目标")),
  .section-body h2:has(+ ul li) { }

  /* 列表 */
  .chapter-body ul, .chapter-body ol, .section-body ul, .section-body ol {
    margin: 10px 0 10px 24px; padding-left: 8px;
  }
  .chapter-body li, .section-body li { margin: 4px 0; line-height: 1.72; }
  .chapter-body li::marker, .section-body li::marker { color: var(--ch-accent); opacity: 0.7; }

  /* ===== 趣味引用块：对话气泡 / 提示卡 / 记忆点 / 深挖 ===== */
  .chapter-body blockquote, .section-body blockquote {
    position: relative;
    margin: 16px 0;
    padding: 14px 20px 14px 62px;
    border-radius: 8px;
    border-left: 4px solid #c8a25d;
    background: var(--bg-quote);
    color: var(--text-soft);
    font-size: 0.875em;
    line-height: 1.7;
    max-width: none;
    box-shadow: 0 1px 2px rgba(0,0,0,0.04);
  }
  .chapter-body blockquote p, .section-body blockquote p { margin: 4px 0; color: var(--text-soft); line-height: 1.7; }
  /* 头像 emoji：固定在左侧 */
  .q-avatar {
    position: absolute;
    left: 16px;
    top: 50%;
    transform: translateY(-50%);
    font-size: 24px;
    line-height: 1;
    filter: drop-shadow(0 1px 1px rgba(0,0,0,0.12));
    user-select: none;
  }
  /* 对话气泡：更"聊天"一点，相邻气泡留出清晰间隔 */
  .chapter-body blockquote.quote-chat, .section-body blockquote.quote-chat {
    background: var(--bg-quote);
    border-left-color: var(--ch-accent, #1971c2);
    margin: 12px 0;
    padding: 12px 20px 12px 60px;
    border: 1px solid var(--border-soft);
    border-left: 4px solid var(--ch-accent, #1971c2);
    border-radius: 10px 8px 8px 10px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
  }
  /* 连续对话气泡成组紧凑；气泡与前后段落之间保持呼吸感 */
  .chapter-body blockquote.quote-chat + blockquote.quote-chat,
  .section-body blockquote.quote-chat + blockquote.quote-chat {
    margin-top: 6px;
  }
  /* 气泡头像：对齐气泡内边距区域，视觉贴首行，短气泡下也稳定居中 */
  .chapter-body blockquote.quote-chat .q-avatar,
  .section-body blockquote.quote-chat .q-avatar {
    left: 14px;
  }
  /* 小贴士：绿意 */
  .chapter-body blockquote.quote-tip, .section-body blockquote.quote-tip {
    border-left-color: #2f9e44;
    background: #f0f9f0;
    border: 1px solid #c9e8c9;
    border-left: 4px solid #2f9e44;
  }
  /* 踩坑警告：橙红 */
  .chapter-body blockquote.quote-warn, .section-body blockquote.quote-warn {
    border-left-color: #e8590c;
    background: #fdf3ec;
    border: 1px solid #f2d2bf;
    border-left: 4px solid #e8590c;
  }
  /* 记忆点：蓝紫 */
  .chapter-body blockquote.quote-note, .section-body blockquote.quote-note {
    border-left-color: #7048e8;
    background: #f4f1fc;
    border: 1px solid #dcd2f5;
    border-left: 4px solid #7048e8;
  }
  /* 深挖：蓝 */
  .chapter-body blockquote.quote-deep, .section-body blockquote.quote-deep {
    border-left-color: #1971c2;
    background: #eef5fc;
    border: 1px solid #c9ddf2;
    border-left: 4px solid #1971c2;
  }
  /* 暗色模式：低亮度底色，保证对比度 */
  [data-theme="dark"] .chapter-body blockquote.quote-chat, [data-theme="dark"] .section-body blockquote.quote-chat {
    background: #262a33;
    border: 1px solid #3a4150;
    border-left: 4px solid var(--ch-accent, #1971c2);
  }
  [data-theme="dark"] .chapter-body blockquote.quote-tip, [data-theme="dark"] .section-body blockquote.quote-tip { background: rgba(47,158,68,0.12); border: 1px solid rgba(47,158,68,0.35); border-left: 4px solid #2f9e44; }
  [data-theme="dark"] .chapter-body blockquote.quote-warn, [data-theme="dark"] .section-body blockquote.quote-warn { background: rgba(232,89,12,0.12); border: 1px solid rgba(232,89,12,0.35); border-left: 4px solid #e8590c; }
  [data-theme="dark"] .chapter-body blockquote.quote-note, [data-theme="dark"] .section-body blockquote.quote-note { background: rgba(112,72,232,0.12); border: 1px solid rgba(112,72,232,0.35); border-left: 4px solid #7048e8; }
  [data-theme="dark"] .chapter-body blockquote.quote-deep, [data-theme="dark"] .section-body blockquote.quote-deep { background: rgba(25,113,194,0.12); border: 1px solid rgba(25,113,194,0.35); border-left: 4px solid #1971c2; }

  /* ===== 思维导图（思维导图标记 :::mindmap 转换的代码块用浅色） ===== */
  .mindmap-block {{
    background: #f7f3eb !important;
    border-color: #e8e0d0 !important;
    border-left: 4px solid var(--ch-accent, #1971c2) !important;
    box-shadow: 0 2px 6px rgba(0,0,0,0.04) !important;
  }}
  .mindmap-block .code-header {{
    background: #ece5d4 !important;
    border-bottom-color: #d4cab8 !important;
  }}
  .mindmap-block .code-lang {{
    color: #5c5c5c !important;
  }}
  .mindmap-block pre {{
    background: #f7f3eb !important;
    color: #2c2c2c !important;
  }}
  [data-theme="dark"] .mindmap-block {{ background: #2a2d35 !important; }}
  [data-theme="dark"] .mindmap-block pre {{ background: #2a2d35 !important; color: #e8e6e3 !important; }}

  /* ===== 行内代码 ===== */
  .chapter-body code, .section-body code {{
    background: #f0e9d8;
    padding: 2px 6px;
    border-radius: 3px;
    font-family: "SF Mono", "Menlo", "Consolas", "Monaco", monospace;
    font-size: 0.88em;
    color: #c92a2a;
    border: 1px solid #e8e0d0;
  }}
  [data-theme="dark"] .chapter-body code, [data-theme="dark"] .section-body code {{ color: #ff8a80; background: #2a2d35; border-color: #3a4150; }}

  /* ===== 代码块容器（带复制按钮 + 语言标签）- 深色专业风格 ===== */
  .code-block {{
    margin: 20px 0;
    border: 1px solid #1a1d23;
    border-radius: 10px;
    overflow: hidden;
    max-width: none;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    background: #1e2128;
  }}
  .code-header {{
    background: #2a2d35;
    padding: 8px 14px;
    display: flex; justify-content: space-between; align-items: center;
    border-bottom: 1px solid #0d0f12;
    font-size: 11px;
  }}
  .code-lang {{
    color: #9ca3af;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1px;
    font-family: "SF Mono", monospace;
  }}
  .code-copy {{
    background: transparent;
    border: 1px solid #4a4d55;
    color: #d1d5db;
    padding: 3px 12px;
    border-radius: 4px;
    cursor: pointer;
    font-size: 11px;
    font-family: inherit;
    transition: all 0.15s;
  }}
  .code-copy:hover {{ background: var(--ch-accent); color: white; border-color: var(--ch-accent); }}
  .code-copy.copied {{ background: #2f9e44; color: white; border-color: #2f9e44; }}
  .code-block pre {{
    background: #1e2128;
    color: #f8f8f2;
    padding: 18px 22px;
    border-radius: 0;
    overflow-x: auto;
    margin: 0;
    line-height: 1.7;
    border: none;
  }}
  .code-block pre code {{
    background: none; color: inherit; padding: 0; font-size: 0.875em;
    border: none;
    font-family: "SF Mono", "Menlo", "Consolas", "Monaco", "Cascadia Code", monospace;
  }}
  /* 代码块内 strong/em 保持代码原色，不被正文强调色污染 */
  .code-block pre code strong, .code-block pre code em {{
    color: inherit; font-style: normal; font-weight: inherit;
  }}

  /* ===== 表格 (专业感) ===== */
  .table-wrap {
    max-width: none;
    margin: 16px 0;
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
    border-radius: 10px;
  }
  .table-wrap table {
    margin: 0;
    max-width: none;
    width: 100%;
  }
  .chapter-body table, .section-body table {{
    border-collapse: separate;
    border-spacing: 0;
    width: 100%;
    margin: 16px 0;
    font-size: 0.875em;
    max-width: none;
    border: 1px solid var(--border);
    border-radius: 10px;
    overflow: hidden;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
  }}
  .chapter-body th, .section-body th {{
    background: var(--ch-accent);
    color: white;
    font-weight: 600;
    padding: 12px 16px;
    text-align: left;
    font-size: 0.85em;
    letter-spacing: 0.02em;
    white-space: nowrap;
  }}
  .chapter-body td, .section-body td {{
    padding: 11px 16px;
    border-bottom: 1px solid var(--border-soft);
    line-height: 1.65;
    vertical-align: top;
  }}
  .chapter-body tr:nth-child(even) td, .section-body tr:nth-child(even) td {{
    background: var(--bg-quote);
  }}
  .chapter-body tr:last-child td, .section-body tr:last-child td {{ border-bottom: none; }}
  .chapter-body tr:hover td, .section-body tr:hover td {{ background: var(--bg-code); }}
  /* 对比表格：首列（维度列）高亮，帮助横向对比 */
  .chapter-body td:first-child, .section-body td:first-child {{
    font-weight: 600;
    color: var(--text);
    background: var(--bg-code);
    white-space: nowrap;
  }}
  .chapter-body tr:nth-child(even) td:first-child, .section-body tr:nth-child(even) td:first-child {{
    background: var(--bg-quote);
  }}
  .chapter-body tr:hover td:first-child, .section-body tr:hover td:first-child {{ background: var(--bg-code); }}
  /* 暗色模式：表头加深对比度，避免纯白刺眼 */
  [data-theme="dark"] .chapter-body th, [data-theme="dark"] .section-body th {{
    background: var(--ch-accent, #1971c2);
    color: #fff;
    filter: brightness(1.25) saturate(0.9);
  }}
  [data-theme="dark"] .chapter-body td:first-child, [data-theme="dark"] .section-body td:first-child {{
    background: rgba(255,255,255,0.04);
  }}
  [data-theme="dark"] .chapter-body tr:nth-child(even) td:first-child, [data-theme="dark"] .section-body tr:nth-child(even) td:first-child {{
    background: rgba(255,255,255,0.02);
  }}

  /* ===== 图片 ===== */
  .chapter-body img, .section-body img {
    max-width: 100%;
    height: auto;
    display: block;
    margin: 16px auto;
    border-radius: 6px;
    border: 1px solid var(--border);
  }

  /* ===== 缺失图片占位 ===== */
  .missing-img {
    display: block;
    margin: 16px auto;
    text-align: center;
  }

  /* ===== 进度条 ===== */
  .progress-bar {{
    position: fixed; top: 53px; left: 0; height: 2px;
    background: linear-gradient(90deg, #42b883, #1971c2);
    z-index: 200;
    width: 0;
    transition: width 0.1s;
  }}

  /* ===== 返回顶部 ===== */
  .back-top {
    position: fixed; bottom: 30px; right: 30px;
    width: 44px; height: 44px;
    background: var(--ch-accent, #1971c2);
    color: white;
    border: none; border-radius: 50%;
    font-size: 20px; cursor: pointer;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    opacity: 0; pointer-events: none;
    transition: opacity 0.2s, transform 0.2s;
    z-index: 90;
  }
  .back-top.visible { opacity: 1; pointer-events: auto; }
  .back-top:hover { transform: translateY(-3px); }

  /* ===== 滚动行为 ===== */
  :target { scroll-margin-top: 70px; }
  ::-webkit-scrollbar { width: 8px; height: 8px; }
  ::-webkit-scrollbar-track { background: transparent; }
  ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 4px; }
  ::-webkit-scrollbar-thumb:hover { background: var(--text-faint); }

  /* ===== 响应式 ===== */
  @media (max-width: 1280px) {
    .content { padding: 28px 28px 60px; }
    .chapter { max-width: 1000px; }
  }
  @media (max-width: 900px) {
    .layout { flex-direction: column; }
    .sidebar { width: 100%; height: auto; max-height: 280px; position: static; border-right: none; border-bottom: 1px solid var(--border); }
    .content { padding: 20px; }
    .chapter { padding: 22px 20px; }
    .chapter-body { padding: 6px 20px 30px; }
    .chapter-body p, .section-body p { line-height: 1.78; }
  }

  /* ===== 打印样式 ===== */
  @media print {
    .topbar, .sidebar, .back-top, .progress-bar, .code-copy, .code-lang { display: none !important; }
    .layout { display: block; max-width: none; margin: 0; padding: 0; }
    .content { padding: 0 !important; }
    .chapter { max-width: none !important; box-shadow: none; border: 1px solid #ccc; border-radius: 0; margin-bottom: 24px; page-break-after: always; }
    .chapter:last-child { page-break-after: auto; }
    .chapter-cover { padding: 24px 20px; }
    .chapter-body { padding: 4px 24px 24px; }
    .section, .chapter-body { break-inside: auto; }
    .code-block, .table-wrap, .markmap, blockquote, figure, .h2-goals { break-inside: avoid; }
    .code-block { max-width: none; box-shadow: none; }
    .table-wrap { max-width: none; overflow: visible; }
    body { background: #fff !important; color: #000 !important; }
    .chapter-body p, .section-body p { max-width: none; }
    [data-theme="dark"] body, [data-theme="dark"] .chapter, [data-theme="dark"] .code-block { background: #fff !important; }
    [data-theme="dark"] .code-block pre { background: #f6f6f6 !important; }
    [data-theme="dark"] .code-block pre code { color: #222 !important; }
    [data-theme="dark"] .chapter-body h1, [data-theme="dark"] .chapter-body h2, [data-theme="dark"] .chapter-body h3,
    [data-theme="dark"] .chapter-body p, [data-theme="dark"] .section-body p { color: #000 !important; }
  }
</style>
</head>
<body class="font-normal">

<div class="progress-bar" id="progressBar"></div>

<div class="topbar">
  <h1>📘 Vue 3 教程 — 预览</h1>
  <div class="topbar-tools">
    <div class="meta" style="margin-right: 12px;">12 章 · 64 课时</div>
    <button class="tool-btn" onclick="setFontSize('small')" id="btn-small">A−</button>
    <button class="tool-btn active" onclick="setFontSize('normal')" id="btn-normal">A</button>
    <button class="tool-btn" onclick="setFontSize('large')" id="btn-large">A+</button>
    <button class="tool-btn" onclick="toggleTheme()" id="btn-theme">🌓</button>
  </div>
</div>

<div class="layout">
  <nav class="sidebar">
    <div class="nav-toolbar">
      <button type="button" class="nav-tool-btn" id="navExpandAll">全部展开</button>
      <button type="button" class="nav-tool-btn" id="navCollapseAll">全部收起</button>
    </div>
    {nav}
  </nav>
  <main class="content">{content}</main>
</div>

<button class="back-top" id="backTop" onclick="window.scrollTo({top: 0, behavior: 'smooth'})">↑</button>

<script>
  // 字号切换
  function setFontSize(size) {
    document.body.classList.remove('font-small', 'font-normal', 'font-large');
    document.body.classList.add('font-' + size);
    document.querySelectorAll('.tool-btn[id^="btn-"]').forEach(b => b.classList.remove('active'));
    const btn = document.getElementById('btn-' + size);
    if (btn) btn.classList.add('active');
    if (size !== 'theme') localStorage.setItem('fontSize', size);
  }

  // 主题切换
  function toggleTheme() {
    const html = document.documentElement;
    const cur = html.getAttribute('data-theme');
    const next = cur === 'dark' ? 'light' : 'dark';
    html.setAttribute('data-theme', next);
    localStorage.setItem('theme', next);
  }

  // 复制代码
  function copyCode(btn) {
    const block = btn.closest('.code-block');
    const code = block.querySelector('pre code').innerText;
    navigator.clipboard.writeText(code).then(() => {
      const orig = btn.innerText;
      btn.innerText = '已复制 ✓';
      btn.classList.add('copied');
      setTimeout(() => {
        btn.innerText = orig;
        btn.classList.remove('copied');
      }, 1500);
    });
  }

  // ===== 折叠式导航 =====
  // 点击章标题：切换展开 + 原生锚点跳转（浏览器默认行为保留）
  document.querySelectorAll('.nav-chapter-title').forEach(title => {
    title.addEventListener('click', () => {
      title.closest('.nav-chapter').classList.toggle('open');
    });
  });
  // 点击小节标题（含 h2 子列表）：切换展开 + 原生锚点跳转
  document.querySelectorAll('.nav-sub-item.has-sub > .nav-sub').forEach(sub => {
    sub.addEventListener('click', () => {
      sub.closest('.nav-sub-item').classList.toggle('open');
    });
  });
  // 全部展开 / 全部收起
  document.getElementById('navExpandAll').addEventListener('click', () => {
    document.querySelectorAll('.nav-chapter, .nav-sub-item').forEach(el => el.classList.add('open'));
  });
  document.getElementById('navCollapseAll').addEventListener('click', () => {
    document.querySelectorAll('.nav-chapter, .nav-sub-item').forEach(el => el.classList.remove('open'));
  });

  // 滚动时：自动展开当前所在章节，其余收起（保持侧边栏简洁）
  let lastAutoCh = '';
  function syncNavFromScroll() {
    const sections = document.querySelectorAll('.chapter');
    const navLinks = document.querySelectorAll('.nav-chapter-title');
    // 判定阈值随视口高度微调：固定 120px 在矮屏/高屏下切换手感不一致
    const threshold = Math.min(200, Math.max(120, Math.round(window.innerHeight * 0.2)));
    let currentCh = '';
    sections.forEach(sec => {
      const rect = sec.getBoundingClientRect();
      // 章顶进入阈值区域、且章底尚未完全滚出视口：防止短章滚过后仍被误判为当前章
      if (rect.top <= threshold && rect.bottom > 0) currentCh = sec.id;
    });
    navLinks.forEach(link => {
      const target = link.getAttribute('href').slice(1);
      link.classList.toggle('nav-active', target === currentCh);
    });
    if (currentCh && currentCh !== lastAutoCh) {
      lastAutoCh = currentCh;
      document.querySelectorAll('.nav-chapter').forEach(item => {
        const link = item.querySelector(':scope > .nav-chapter-title');
        const open = link && link.getAttribute('href') === '#' + currentCh;
        item.classList.toggle('open', open);
      });
    }
  }

  // 进度条 + 返回顶部 + 章节高亮（滚动时同步折叠状态）
  window.addEventListener('scroll', () => {
    const h = document.documentElement.scrollHeight - window.innerHeight;
    const pct = h > 0 ? (window.scrollY / h) * 100 : 0;
    document.getElementById('progressBar').style.width = pct + '%';
    document.getElementById('backTop').classList.toggle('visible', window.scrollY > 400);
    syncNavFromScroll();
  });

  // 初始化
  const savedFont = localStorage.getItem('fontSize');
  if (savedFont) setFontSize(savedFont);
  const savedTheme = localStorage.getItem('theme');
  if (savedTheme) document.documentElement.setAttribute('data-theme', savedTheme);
  // 首屏/带 #锚点打开时即同步导航高亮与展开状态（此前仅在 scroll 事件触发）
  syncNavFromScroll();

  // 纯 CSS 锚点导航，无 JS 干预
</script>

</body>
</html>
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", help="教材根目录")
    parser.add_argument("output", help="输出的 HTML 路径")
    args = parser.parse_args()

    source = Path(args.source).expanduser().resolve()
    output = Path(args.output).expanduser().resolve()

    if not source.is_dir():
        print(f"Error: {source} not found", file=sys.stderr)
        sys.exit(1)

    print(f"扫描: {source}")
    chapters = collect_chapter_files(source)
    print(f"找到 {len(chapters)} 章/总览")

    nav = make_nav(chapters)
    content = "\n".join(make_chapter_html(ch) for ch in chapters)

    img_map = build_image_map(source)
    if img_map:
        content = rewrite_image_src(content, img_map)
        print(f"图片映射: {len(img_map)//2} 个文件")

    title = "Vue 3 教程"
    html = (HTML_TEMPLATE
            .replace("{title}", title)
            .replace("{nav}", nav)
            .replace("{content}", content)
            .replace("{{", "{")
            .replace("}}", "}"))
    output.write_text(html, encoding="utf-8")

    size_kb = output.stat().st_size / 1024
    print(f"✅ 已生成: {output}  ({size_kb:.1f} KB)")


if __name__ == "__main__":
    main()