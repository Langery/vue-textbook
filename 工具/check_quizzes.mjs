/**
 * check_quizzes.mjs — 校验各章小测的答案表质量。
 *
 * 教材的「本章小测」是学生唯一的自我检测手段，答案表如果只给个字母，
 * 错题复习时无从下手。所以检查三件事：
 *   ① 答案表存在，且题号与题目一一对应（不漏题）
 *   ② 每题都有解析（不是只有答案字母）
 *   ③ 解析不是敷衍（太短的提示不算解析）
 */
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const BOOK = path.join(__dirname, '..', '教材')

function walk(dir, out = []) {
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, e.name)
    if (e.isDirectory()) walk(p, out)
    else if (e.name.endsWith('.md')) out.push(p)
  }
  return out
}

const files = walk(BOOK).filter((f) => f.includes('本章小测'))
let issues = 0

for (const f of files) {
  const md = fs.readFileSync(f, 'utf-8')
  const sec = path.basename(f).split('-')[0]
  const problems = []

  // 答案表起点：形如 "## 📊 参考答案" / "## ✅ 答案" / "## 📝 答案与解析"
  const ansIdx = md.search(/^##\s*.*(?:参考答案|答案与解析|答案)/m)
  if (ansIdx < 0) {
    problems.push('找不到答案表')
  } else {
    const quiz = md.slice(0, ansIdx)
    const ans = md.slice(ansIdx)

    // 题目里的题号
    const qNums = new Set()
    for (const m of quiz.matchAll(/(?:^###\s+|^\*\*|#{2,3}\s+)(\d+)\s*[.、]/gm)) {
      qNums.add(+m[1])
    }
    // 表格形式的题目（| 题号 | ...）
    for (const m of quiz.matchAll(/^\|\s*(\d+)\s*\|/gm)) qNums.add(+m[1])

    // 答案表里的题号
    const aNums = new Set()
    for (const m of ans.matchAll(/^\|\s*(\d+)\s*\|/gm)) aNums.add(+m[1])
    // 简答形式："1. C  2. C"
    for (const m of ans.matchAll(/^\s*(\d+)\s*[.、]\s*[A-D✅❌]/gm)) aNums.add(+m[1])
    // 简答/代码题形如 "**13. 说明**：" —— 也算有答案
    for (const m of ans.matchAll(/^\s*\*\*(\d+)\s*[.、]/gm)) aNums.add(+m[1])

    // 只对「客观题」查漏：代码题/简答题的答案常写成段落形式，不在表里
    const objective = [...qNums].filter((n) => {
      // 找到该题的上下文，判断题型
      const idx = quiz.indexOf(`### ${n}.`)
      const ctx = idx >= 0 ? quiz.slice(idx, idx + 400) : ''
      // 客观题的标志：选项列表 A. B. C. D. 或"判断"字样
      return /[-*]\s*A\.|A\.\s*\S.*B\.\s*\S|判断题|选择题|填空题/.test(ctx)
    })

    const missing = objective.filter((n) => !aNums.has(n)).sort((a, b) => a - b)
    if (missing.length) {
      problems.push(`答案表漏了第 ${missing.join(', ')} 题（客观题共 ${objective.length} 道）`)
    }

    // 解析质量：表格第三列
    const rows = [...ans.matchAll(/^\|\s*(\d+)\s*\|\s*[^|]*\|\s*([^|]*)\|/gm)]
    const thin = []
    for (const [, num, expl] of rows) {
      const text = expl.trim()
      if (!text || text.length < 8) thin.push(num)
    }
    if (thin.length) {
      problems.push(`第 ${thin.join(', ')} 题解析过短（少于 8 字）`)
    }
  }

  if (problems.length) {
    issues++
    console.log(`❌ ${sec} ${path.basename(f)}`)
    for (const p of problems) console.log(`     ${p}`)
  }
}

console.log(`\n检查 ${files.length} 个小测，${issues} 个有问题`)
if (!issues) console.log('全部通过 🎉')
else process.exitCode = 1
