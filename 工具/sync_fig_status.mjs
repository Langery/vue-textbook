/**
 * sync_fig_status.mjs — 同步各章 README 的配图表状态。
 *
 * 背景：配图画完后，README 里的「本章配图」表格还写着「待做」，
 * 读者一看以为缺图。表格状态必须跟实际文件 + 正文引用保持一致。
 *
 * 只处理「图号 | 主题 | 状态」这种表格（第 3 列是"已完成/待做"）。
 * 第 1 章那种「图号 | 主题 | 位置(链接)」格式的表不动 —— 它没有状态列。
 */
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const ROOT = path.resolve(__dirname, '..')
const BOOK = path.join(ROOT, '教材')
const IMG = path.join(ROOT, '配图')

/** 收集全书正文对图的引用：图号 → 引用它的小节名 */
function collectRefs() {
  const refs = new Map()
  const walk = (dir) => {
    for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
      const p = path.join(dir, e.name)
      if (e.isDirectory()) walk(p)
      else if (e.name.endsWith('.md')) {
        const md = fs.readFileSync(p, 'utf-8')
        const sec = path.basename(p, '.md')
        for (const m of md.matchAll(/配图\/[^)"\s]*\/图(\d+-\d+)\.svg/g)) {
          const id = m[1]
          if (!refs.has(id)) refs.set(id, new Set())
          refs.get(id).add(sec)
        }
      }
    }
  }
  walk(BOOK)
  return refs
}

const refs = collectRefs()
let changed = 0
let skipped = 0

for (const chDir of fs.readdirSync(BOOK)) {
  const chPath = path.join(BOOK, chDir)
  if (!fs.statSync(chPath).isDirectory()) continue
  const readme = path.join(chPath, 'README.md')
  if (!fs.existsSync(readme)) continue

  const lines = fs.readFileSync(readme, 'utf-8').split('\n')

  const headIdx = lines.findIndex((l) => /^##\s*📚\s*本章配图/.test(l))
  if (headIdx < 0) continue

  // 找表头行
  let tableStart = -1
  for (let i = headIdx; i < Math.min(headIdx + 20, lines.length); i++) {
    if (/^\|\s*图号\s*\|/.test(lines[i])) { tableStart = i; break }
  }
  if (tableStart < 0) continue

  // 表头第三列必须是「状态」，否则这张表没有状态列，不动它
  const headerCols = lines[tableStart].split('|').map((c) => c.trim()).filter(Boolean)
  if (!headerCols.includes('状态')) { skipped++; continue }

  // 定位表格结束行
  let tableEnd = tableStart + 1
  while (tableEnd < lines.length && lines[tableEnd].trim().startsWith('|')) tableEnd++

  let done = 0
  let total = 0
  let modified = false
  const out = []

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i]

    if (i === tableStart) {
      out.push('| 图号 | 主题 | 状态 | 正文引用 |')
      continue
    }

    if (i > tableStart && i < tableEnd) {
      // 分隔行
      if (!/^\|\s*\d+-\d+\s*\|/.test(line)) {
        out.push('|---|---|---|---|')
        continue
      }
      const row = line.match(/^\|\s*(\d+-\d+)\s*\|(.*?)\|\s*(已完成|待做)\s*\|(?:\s*([^|]*?)\s*\|)?\s*$/)
      if (!row) { out.push(line); continue }

      const id = row[1]
      const topic = row[2].trim()
      const file = path.join(IMG, chDir, `图${id}.svg`)
      const exists = fs.existsSync(file)
      const status = exists ? '已完成' : '待做'
      if (exists) done++
      total++

      const hit = refs.get(id)
      let refCell
      if (!hit) refCell = exists ? '⚠️ 未被引用' : '—'
      else {
        const list = [...hit].map((s) => s.split('-')[0])
        refCell = list.length > 2 ? `${list.slice(0, 2).join('、')} 等 ${list.length} 处` : list.join('、')
      }

      const newLine = `| ${id} | ${topic} | ${status} | ${refCell} |`
      if (newLine !== line) modified = true
      out.push(newLine)
      continue
    }

    out.push(line)
  }

  // 更新标题里的统计
  {
    const head = out[headIdx]
    const newHead = head.replace(/（规划 \d+ 张 \/ 已完成 \d+ 张）/,
      `（规划 ${total} 张 / 已完成 ${done} 张）`)
    if (newHead !== head) { out[headIdx] = newHead; modified = true }
  }

  if (modified) {
    fs.writeFileSync(readme, out.join('\n'))
    changed++
    console.log(`  ✅ ${chDir}/README.md —— 共 ${total} 张，已完成 ${done} 张`)
  }
}

console.log(`\n同步 ${changed} 个章 README，跳过 ${skipped} 个（无状态列）`)
