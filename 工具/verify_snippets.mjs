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

/**
 * 编译期查不出的问题：用了 Vue 的 API 但忘了 import。
 * 例：store 里写了 ref(...) 却只 import 了 defineStore —— 编译能过，运行时才炸。
 *
 * 注意：defineProps / defineEmits / defineExpose / defineModel / defineOptions
 * 是**编译器宏**，由 SFC 编译器自动注入，**不需要 import**（import 反而会报错）。
 * 所以它们不在检查列表里。
 */
const VUE_APIS = [
  'ref', 'reactive', 'computed', 'watch', 'watchEffect', 'shallowRef', 'shallowReactive',
  'toRef', 'toRefs', 'toRaw', 'markRaw', 'unref', 'isRef', 'isReactive', 'isProxy',
  'nextTick', 'onMounted', 'onUnmounted', 'onBeforeMount', 'onBeforeUnmount', 'onUpdated',
  'onBeforeUpdate', 'onActivated', 'onDeactivated', 'onErrorCaptured', 'onWatcherCleanup',
  'onScopeDispose', 'effectScope', 'getCurrentScope', 'provide', 'inject',
  'useAttrs', 'useSlots', 'useTemplateRef'
]

/** 编译器宏：不需要 import */
const COMPILER_MACROS = [
  'defineProps', 'defineEmits', 'defineExpose', 'defineModel', 'defineOptions',
  'defineSlots', 'useModel'
]

function checkMissingImports(code) {
  const issues = []
  const scriptMatch = code.match(/<script[^>]*>([\s\S]*?)<\/script>/)
  if (!scriptMatch) return issues
  const script = scriptMatch[1]

  // 收集已导入的名字
  const imported = new Set()
  const importRe = /import\s*\{([^}]*)\}\s*from\s*['"][^'"]+['"]/g
  let m
  while ((m = importRe.exec(script))) {
    for (const part of m[1].split(',')) {
      const name = part.trim().split(/\s+as\s+/).pop().trim()
      if (name) imported.add(name)
    }
  }
  // import * as X
  if (/import\s+\*\s+as\s+(\w+)/.test(script)) {
    imported.add(/import\s+\*\s+as\s+(\w+)/.exec(script)[1])
  }

  for (const api of VUE_APIS) {
    // 用了它：后面跟 (
    const usage = new RegExp(`(?<![\\w.$])${api}\\s*\\(`).test(script)
    if (!usage) continue
    if (imported.has(api)) continue
    // 局部定义同名变量则忽略
    if (new RegExp(`(const|let|var|function)\\s+${api}\\b`).test(script)) continue
    issues.push(`使用了 ${api} 但没有 import`)
  }
  return issues
}

/**
 * 教学片段豁免：教材里有大量代码块是「只讲这一行怎么写」的片段，
 * 本来就不该带完整 import。这类不报漏 import。
 *
 * 判断依据：script 里**完全没有 import 语句** → 是片段；
 * 有 import 但缺某个 → 是真的漏，要报。
 */
function isFragmentSnippet(code) {
  const scriptMatch = code.match(/<script[^>]*>([\s\S]*?)<\/script>/)
  if (!scriptMatch) return false
  const script = scriptMatch[1]
  return !/^\s*import\s/m.test(script)
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
    // 编译过了不代表能跑——再查一遍漏 import
    if (!isFragmentSnippet(code)) {
      const missing = checkMissingImports(code)
      if (missing.length) {
        return { status: 'fail', reason: '漏 import: ' + missing.join('; ') }
      }
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
