/**
 * gen_glossary.mjs — 扫描教材，定位每个术语的「首次讲解处」，生成术语索引。
 *
 * 判定「讲解处」而不是「提及处」：只看标题行（## / ###）里出现该术语，
 * 说明这一节就是在讲它。正文里顺带提到的不算。
 */
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const BOOK = path.join(__dirname, '..', '教材')

// 术语 → 中文说明
const TERMS = {
  // 响应式
  ref: '把任意值包成 `.value` 的响应式引用，单值/独立值首选',
  reactive: '把对象变成响应式的 Proxy，多字段状态首选',
  computed: '基于依赖缓存的派生值，同步、有缓存',
  watch: '监听数据变化做副作用，默认惰性（需 immediate 才立即跑）',
  watchEffect: '自动收集依赖的副作用，立即执行一次',
  shallowRef: '只有第一层响应式的 ref，深层改动需手动 triggerRef',
  shallowReactive: '只有第一层响应式的 reactive',
  toRef: '把对象的某个属性单独转成 ref，保持与原对象的联动',
  toRefs: '把 reactive 对象的每个属性转成独立 ref，解构后不丢响应式',
  toRaw: '拿到响应式对象的原始对象（跳过 Proxy）',
  markRaw: '给对象贴"别代理我"的标签，用于第三方实例',
  readonly: '深度只读代理，写入被拦截不生效',
  unref: '传参时把 ref 自动解包成普通值',
  isRef: '判断一个值是不是 ref',
  isReactive: '判断一个值是不是响应式对象',
  nextTick: '等本次 DOM 更新完成（Vue 3.5 起也可 `await` 后自然生效）',
  customRef: '自定义 ref，自己控制依赖收集与触发',
  triggerRef: '手动触发 shallowRef 的更新',
  // 组件
  defineProps: '声明组件接收的 props（编译器宏，无需 import）',
  defineEmits: '声明组件触发的事件（编译器宏，无需 import）',
  defineModel: '声明双向绑定的 prop + emit（编译器宏，Vue 3.4+）',
  defineExpose: '暴露组件内部方法给父组件',
  defineOptions: '声明组件选项（name / inheritAttrs 等）',
  useTemplateRef: '获取模板 ref 的新方式（Vue 3.5+）',
  Teleport: '把组件内容渲染到 DOM 树的别处（弹窗、抽屉）',
  Suspense: '处理异步组件加载状态的边界组件',
  KeepAlive: '缓存已渲染过的组件实例，切换时保留状态',
  Fragment: '多根节点片段，Vue 3 起模板可有多根',
  // 组合式
  provide: '向后代组件提供数据（可传响应式对象）',
  inject: '从祖先组件接收 provide 的数据',
  effectScope: '批量管理作用域内的副作用，可一次性停止',
  onWatcherCleanup: '注册 watcher 的清理函数（Vue 3.5+）',
  onScopeDispose: '作用域销毁时执行的清理（effectScope 配套）',
  // 路由与状态
  defineStore: '定义一个 Pinia store',
  storeToRefs: '解构 store 时保持响应式（Pinia 专用）',
  useRouter: '在 setup 里拿到 router 实例',
  useRoute: '在 setup 里拿到当前路由对象',
  RouterLink: '声明式路由跳转组件',
  RouterView: '路由视图出口组件',
  // 指令
  vModel: '双向绑定指令',
  vFor: '列表渲染指令',
  vIf: '条件渲染指令（销毁/重建）',
  vShow: '条件显示指令（切换 display）',
  vBind: '绑定属性指令',
  vOn: '绑定事件指令',
  vHtml: '渲染原始 HTML（有 XSS 风险）',
  vText: '渲染纯文本（自动转义）',
  vMemo: '缓存子树渲染结果，大列表优化',
  vPre: '跳过编译，原样输出',
  vOnce: '只渲染一次',
  vBindSync: '（已废弃）双向绑定的旧写法'
}

function walk(dir, out = []) {
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, e.name)
    if (e.isDirectory()) walk(p, out)
    else if (e.name.endsWith('.md')) out.push(p)
  }
  return out
}

const files = walk(BOOK)
  .filter((f) => !f.endsWith('README.md') && !f.includes('00-课程总览'))
  .sort()

/** 收集每个文件的小节号与标题行 */
const sections = files.map((f) => {
  const md = fs.readFileSync(f, 'utf-8')
  const sec = path.basename(f).split('-')[0]
  const title = (md.match(/^#\s+(.+)$/m) || [, ''])[1].trim()
  const heads = [...md.matchAll(/^#{2,3}\s+(.+)$/gm)].map((m) => m[1].trim())
  return { sec, title, heads, file: path.relative(BOOK, f) }
})

// 定位每个术语的讲解处
//
// 「讲解处」优先：标题里术语出现在开头（形如「💡 二、ref 基础用法」或「ref 是什么」），
// 其次：标题里含术语。纯正文提及不算。
// 还要避免命中「Step N：…」「陷阱 N：…」这类操作步骤——那不是概念讲解。
const OPERATION = /^(Step|步骤|Trap|陷阱|练习|实战|案例|📝|🛠\s*第)/i

function isDefinitionHeading(head) {
  if (OPERATION.test(head)) return false
  // 排除纯题目型标题（含「?」「？」结尾的多是练习题）
  if (/[?？]$/.test(head)) return false
  return true
}

const found = {}
for (const [term] of Object.entries(TERMS)) {
  const key = term.replace(/^v([A-Z])/, (m, c) => 'v-' + c.toLowerCase())
  const re = new RegExp(`\\b${key.replace(/[-]/g, '[-]?')}\\b`, 'i')

  // 收集所有候选，按优先级排序
  const candidates = []
  for (const s of sections) {
    for (const h of s.heads) {
      if (!re.test(h)) continue
      if (!isDefinitionHeading(h)) continue
      // 优先级：术语在标题开头 > 标题里含「是/的/：」等定义性结构 > 普通提及
      const startsWith = re.test(h.replace(/^[^\w\u4e00-\u9fa5]+/, ''))
      const definitional = /[：:]|是什么|的(基本|核心|用法|原理|概念)/.test(h)
      let score = 0
      if (startsWith) score += 10
      if (definitional) score += 5
      if (s.title.includes(key)) score += 3
      // 讲这个术语的"正节"（小节主标题就是它）额外加权
      const sTitle = s.title.replace(/^[^\w\u4e00-\u9fa5]+/, '')
      if (sTitle.startsWith(key)) score += 8
      candidates.push({ sec: s.sec, head: h, score, title: s.title })
    }
    // 小节主标题也作为候选（权重最高）
    if (re.test(s.title) && isDefinitionHeading(s.title)) {
      candidates.push({ sec: s.sec, head: s.title, score: 20, title: s.title })
    }
  }

  if (candidates.length) {
    candidates.sort((a, b) => b.score - a.score)
    // 同分或接近时，取章节号更小的（概念通常先系统讲、后对比）
    const top = candidates[0].score
    const near = candidates.filter((c) => c.score >= top - 3)
    near.sort((a, b) => {
      const na = a.sec.split('.').map(Number)
      const nb = b.sec.split('.').map(Number)
      return na[0] - nb[0] || na[1] - nb[1]
    })
    found[term] = near[0]
  }
}

console.log('| 术语 | 含义 | 讲解位置 |')
console.log('|---|---|---|')
const miss = []
for (const [term, desc] of Object.entries(TERMS)) {
  const f = found[term]
  if (!f) { miss.push(term); continue }
  console.log(`| \`${term}\` | ${desc} | ${f.sec} ${f.head} |`)
}
if (miss.length) console.log('\n未定位到讲解处:', miss.join(', '))
