/**
 * verify_snippets.mjs — 校验教材里的 .vue 代码块能否被 Vue 真实编译。
 *
 * 背景：教材的「完整示例」是学生唯一会照抄的东西，一个多余逗号就会
 * 让他们白折腾半小时。本脚本把正文里的 ```vue 代码块逐个喂给
 * @vue/compiler-sfc，语法错误直接报出来。
 *
 * 用法：
 *   node 工具/verify_snippets.mjs                # 校验全部
 *   node 工具/verify_snippets.mjs 03.13          # 只校验节号含 03.13 的
 *   node 工具/verify_snippets.mjs --require-template # 只查「完整组件」类（有 template 的）
 */
import { parse, compileScript, compileTemplate } from '@vue/compiler-sfc'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const ROOT = path.resolve(__dirname, '..')
const BOOK = path.join(ROOT, '教材')

const args = process.argv.slice(2)
const filters = args.filter((a) => !a.startsWith('--'))
const requireTemplate = args.includes('--require-template')

function walk(dir, out = []) {
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, e.name)
    if (e.isDirectory()) walk(p, out)
    else if (e.name.endsWith('.md')) out.push(p)
  }
  return out
}

/** 从 markdown 中抽出所有 ```vue ... ``` 块 */
function extractVueBlocks(md) {
  const blocks = []
  const re = /```vue[^\n]*\n([\s\S]*?)```/g
  let m
  while ((m = re.exec(md))) blocks.push({ code: m[1], index: m.index, line: md.slice(0, m.index).split('\n').length })
  return blocks
}

/**
 * 教学反例不算错误：教材里大量代码块是「故意写错」用来演示报错的，
 * 或者用 `{ ... }` 占位。这些无法通过编译，但也不是缺陷。
 */
const INTENTIONAL_ERROR_HINTS = [
  /❌/, // 反例标记
  /\{\s*\.\.\.\s*\}/, // 伪代码占位
  /不正确/,
  /会报错/,
  /故意违反/,
  /看看.*报错/,
]

function isIntentional(code) {
  return INTENTIONAL_ERROR_HINTS.some((re) => re.test(code))
}

function checkOne(code, label) {
  // 非 SFC 的片段（只含一段 template、或只是插值示例）跳过
  const isSFC = /<script/.test(code) || /<template>/.test(code)
  if (!isSFC) return { status: 'skip', reason: '非完整 SFC' }

  const { descriptor, errors } = parse(code, { filename: 'x.vue' })

  // 多个并列组件（教材常把父子组件写在同一代码块里）不是错误
  const multiBlock =
    (code.match(/<script setup>/g) || []).length > 1 ||
    (code.match(/<template>/g) || []).length > 1

  if (errors.length) {
    if (isIntentional(code) || multiBlock) {
      return { status: 'skip', reason: '教学反例 / 多组件并列' }
    }
    return { status: 'fail', reason: 'parse: ' + errors.map((e) => e.message).join('; ') }
  }

  try {
    if (descriptor.scriptSetup || descriptor.script) {
      compileScript(descriptor, { id: 'x' })
    }
  } catch (e) {
    return { status: 'fail', reason: 'script: ' + e.message }
  }

  if (descriptor.template) {
    const r = compileTemplate({
      source: descriptor.template.content,
      filename: 'x.vue',
      id: 'x'
    })
    if (r.errors.length) {
      return { status: 'fail', reason: 'template: ' + r.errors.map((e) => e.message || e).join('; ') }
    }
    return { status: 'ok', kind: '完整 SFC' }
  }

  if (requireTemplate) return { status: 'skip', reason: '无 template' }
  return { status: 'ok', kind: '仅 script' }
}

const files = walk(BOOK).filter((f) => {
  if (filters.length === 0) return true
  const rel = path.relative(BOOK, f)
  return filters.some((s) => rel.includes(s))
})

let total = 0
let ok = 0
let fail = 0
let skip = 0
const failures = []

for (const f of files) {
  const md = fs.readFileSync(f, 'utf-8')
  const blocks = extractVueBlocks(md)
  for (const b of blocks) {
    total++
    const r = checkOne(b.code, f)
    if (r.status === 'ok') {
      ok++
    } else if (r.status === 'skip') {
      skip++
    } else {
      fail++
      const rel = path.relative(ROOT, f)
      failures.push({ file: rel, line: b.line, reason: r.reason })
    }
  }
}

console.log(`\n检查 ${files.length} 个文件，${total} 个 vue 代码块`)
console.log(`  ✅ 通过 ${ok}   ❌ 失败 ${fail}   ⏭️  跳过 ${skip}\n`)

if (failures.length) {
  console.log('失败明细：')
  for (const x of failures) {
    console.log(`  ${x.file}:${x.line}`)
    console.log(`     ${x.reason.slice(0, 160)}`)
  }
  process.exitCode = 1
} else {
  console.log('全部通过 🎉')
}
