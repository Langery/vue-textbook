/**
 * check_svgs.mjs — 校验配图 SVG 的质量。
 *
 * 教材配图是手写 SVG，出错不会编译报错、只会在页面上显示得很怪。
 * 本脚本检查三件事：
 *   ① 结构合法（能解析、有 viewBox、标签闭合）
 *   ② 文字不溢出画布（按中英文字宽估算）
 *   ③ 文字不互相重叠（包围盒相交）
 *
 * 用法：
 *   node 工具/check_svgs.mjs                # 校验全部
 *   node 工具/check_svgs.mjs 06             # 只校验路径含 06 的
 */
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const ROOT = path.resolve(__dirname, '..')
const IMG_DIR = path.join(ROOT, '配图')

const filters = process.argv.slice(2)

function walk(dir, out = []) {
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, e.name)
    if (e.isDirectory()) walk(p, out)
    else if (e.name.endsWith('.svg')) out.push(p)
  }
  return out
}

/** 估算一段文字的像素宽度：中文按字号，英文按 0.55×字号 */
function textWidth(content, fontSize, isMono) {
  let w = 0
  for (const ch of content) {
    if (/[\u4e00-\u9fa5\uff00-\uffef]/.test(ch)) w += fontSize
    else w += fontSize * (isMono ? 0.6 : 0.55)
  }
  return w
}

function parseTexts(svg) {
  const out = []
  const re = /<text([^>]*)>([\s\S]*?)<\/text>/g
  let m
  while ((m = re.exec(svg))) {
    const attrs = m[1]
    const inner = m[2]
    const fontSize = parseInt((attrs.match(/font-size="(\d+)"/) || [])[1] || '12', 10)
    const x = parseFloat((attrs.match(/\sx="([-\d.]+)"/) || [])[1] || '0')
    const y = parseFloat((attrs.match(/\sy="([-\d.]+)"/) || [])[1] || '0')
    const anchor = (attrs.match(/text-anchor="(\w+)"/) || [])[1] || 'start'
    const isMono = /monospace/.test(attrs)

    // 多行文本用 <tspan x=... dy=...> 排版 —— 每行单独算一个包围盒
    const tspanRe = /<tspan([^>]*)>([^<]*)<\/tspan>/g
    const rows = []
    let tm
    let isMulti = false
    while ((tm = tspanRe.exec(inner))) {
      isMulti = true
      const ta = tm[1]
      const tx = parseFloat((ta.match(/\sx="([-\d.]+)"/) || [])[1] || String(x))
      const dyRaw = (ta.match(/\sdy="([-\d.]+)"/) || [])[1]
      const ty = dyRaw != null ? y + parseFloat(dyRaw) : y
      rows.push({ content: tm[2], x: tx, y: ty })
    }
    if (!isMulti) {
      rows.push({ content: inner.replace(/<[^>]+>/g, ''), x, y })
    }

    for (const row of rows) {
      const w = textWidth(row.content, fontSize, isMono)
      const left = anchor === 'middle' ? row.x - w / 2 : anchor === 'end' ? row.x - w : row.x
      out.push({
        content: row.content,
        x: row.x,
        y: row.y,
        left,
        right: left + w,
        top: row.y - fontSize,
        bottom: row.y + 3,
        fontSize
      })
    }
  }
  return out
}

function checkFile(file) {
  const svg = fs.readFileSync(file, 'utf-8')
  const problems = []

  // ① 结构
  if (!svg.includes('<svg')) problems.push('缺少 <svg> 根元素')
  if (!svg.includes('viewBox')) problems.push('缺少 viewBox（缩放会失真）')
  // 标签配平（简单统计 self-closing 之外的成对标签）
  for (const tag of ['svg', 'g', 'text', 'rect', 'line', 'polygon', 'path', 'circle']) {
    const open = (svg.match(new RegExp(`<${tag}[\\s>]`, 'g')) || []).length
    const close = (svg.match(new RegExp(`</${tag}>`, 'g')) || []).length
    const selfClose = (svg.match(new RegExp(`<${tag}[^>]*/>`, 'g')) || []).length
    if (open - selfClose !== close) {
      problems.push(`<${tag}> 标签不配平（开 ${open} / 自闭合 ${selfClose} / 闭 ${close}）`)
    }
  }

  // ② 文字溢出
  const W = parseInt((svg.match(/width="(\d+)"/) || [])[1] || '720', 10)
  const H = parseInt((svg.match(/height="(\d+)"/) || [])[1] || '340', 10)
  const texts = parseTexts(svg)
  for (const t of texts) {
    if (t.left < -2 || t.right > W + 2) {
      problems.push(`文字超出画布: "${t.content.slice(0, 30)}" (${Math.round(t.left)}~${Math.round(t.right)}, 画布宽 ${W})`)
    }
    if (t.y > H + 2 || t.top < -2) {
      problems.push(`文字纵向超出画布: "${t.content.slice(0, 30)}" (y=${t.y}, 画布高 ${H})`)
    }
  }

  // ③ 文字重叠
  //    判定标准：两段文字的包围盒在垂直方向上真的压到一起才算。
  //    注意不能用「包围盒相交」直接判——中文行高通常大于字号，
  //    标题(13px) + 说明(11px) 相距 12px 是正常的上下堆叠，不是重叠。
  for (let i = 0; i < texts.length; i++) {
    for (let j = i + 1; j < texts.length; j++) {
      const a = texts[i], b = texts[j]
      const overlapX = a.left < b.right && b.left < a.right
      if (!overlapX) continue
      // 垂直方向：基线间距小于较大字号的 90% 才算压字
      const dy = Math.abs(a.y - b.y)
      // 同一基线（dy≈0）且水平相接 —— 那是并排画的一行代码，不是重叠
      if (dy < 1) continue
      const threshold = Math.max(a.fontSize, b.fontSize) * 0.9
      if (dy < threshold) {
        problems.push(`文字重叠: "${a.content.slice(0, 18)}" ↔ "${b.content.slice(0, 18)}" (间距 ${Math.round(dy)} < ${Math.round(threshold)})`)
      }
    }
  }

  return { problems, textCount: texts.length }
}

let files = walk(IMG_DIR)
if (filters.length) files = files.filter((f) => filters.some((s) => f.includes(s)))

let bad = 0
let totalProblems = 0
for (const f of files) {
  const { problems, textCount } = checkFile(f)
  const rel = path.relative(ROOT, f)
  if (problems.length) {
    bad++
    totalProblems += problems.length
    console.log(`❌ ${rel}`)
    for (const p of problems.slice(0, 4)) console.log(`     ${p}`)
    if (problems.length > 4) console.log(`     ...还有 ${problems.length - 4} 个问题`)
  }
}

console.log(`\n检查 ${files.length} 个 SVG，${bad} 个有问题（共 ${totalProblems} 处）`)
if (!bad) console.log('全部通过 🎉')
else process.exitCode = 1
