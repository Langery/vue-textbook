/**
 * insert_figures.mjs — 把已画好的配图插入教材正文对应位置。
 *
 * 背景：配图画在 配图/ 目录里，但正文不引用 = 读者根本看不到。
 * 本脚本按「图号 → 目标小节 + 插入锚点」的映射表批量插入 <img> 引用。
 *
 * 幂等：已插入过的图会跳过，重复运行不会插两次。
 */
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const BOOK = path.join(__dirname, '..', '教材')

// 图号 → { 章节目录, 小节目录, 插入锚点(在该小节文件里要插到哪个标题前), alt }
// 锚点用小节内的二级标题文本匹配，插到该标题**之前**
const FIGS = [
  // ── 第 6 章 ──
  { fig: '图6-3.svg', ch: '06-生命周期与副作用', sec: '06.2-副作用：到底是个啥',
    anchor: '## 💡 二、Vue 组件中哪些是副作用？',
    alt: '副作用概念：纯计算 vs 副作用的对比' },
  { fig: '图6-4.svg', ch: '06-生命周期与副作用', sec: '06.4-watchEffect入门',
    anchor: '## 💡 二、基本语法',
    alt: 'watchEffect 的本质：自动收集依赖与执行副作用' },
  { fig: '图6-5.svg', ch: '06-生命周期与副作用', sec: '06.4-watchEffect入门',
    anchor: '## 🛠 三、完整可运行示例',
    alt: 'watchEffect 基础语法三段结构：立即执行 / 自动收集依赖 / 依赖变化重跑' },
  { fig: '图6-6.svg', ch: '06-生命周期与副作用', sec: '06.4-watchEffect入门',
    anchor: '## 🔍 四、`watchEffect` 的执行时机',
    alt: 'watchEffect 执行时机时间轴：创建 / 挂载 / 变化 / 卸载' },
  { fig: '图6-7.svg', ch: '06-生命周期与副作用', sec: '06.6-清理副作用',
    anchor: '## 💡 二、`onWatcherCleanup`（Vue 3.5+，推荐）',
    alt: '清理函数：忘记清理导致定时器叠加 vs 用 onWatcherCleanup 自动清理' },
  { fig: '图6-8.svg', ch: '06-生命周期与副作用', sec: '06.5-watch精准监听',
    anchor: '## 🆚 五、`computed` vs `watchEffect` vs `watch`',
    alt: 'computed / watchEffect / watch 三者对比' },
  { fig: '图6-9.svg', ch: '06-生命周期与副作用', sec: '06.7-什么时候不该用watch',
    anchor: '## 🧠 本节小结',
    alt: '何时该用 watch、何时不该用 watch' },
  { fig: '图6-10.svg', ch: '06-生命周期与副作用', sec: '06.7-什么时候不该用watch',
    anchor: '## 📝 即时练习',
    alt: '四个常见 watch 反模式及其正确改法' },

  // ── 第 8 章 ──
  { fig: '图8-3.svg', ch: '08-路由与状态管理', sec: '08.3-动态路由匹配',
    anchor: '## 🧠 本节小结',
    alt: 'params 与 query 的对比：路径段参数 vs 查询串参数' },
  { fig: '图8-4.svg', ch: '08-路由与状态管理', sec: '08.4-嵌套路由',
    anchor: '## 🧠 本节小结',
    alt: '嵌套路由：双层 router-view 的渲染关系' },
  { fig: '图8-5.svg', ch: '08-路由与状态管理', sec: '08.5-编程式导航',
    anchor: '## 🧠 本节小结',
    alt: '编程式导航 router.push vs 声明式导航 RouterLink' },
  { fig: '图8-6.svg', ch: '08-路由与状态管理', sec: '08.6-导航守卫：路由保安',
    anchor: '## 🧠 本节小结',
    alt: '导航守卫完整解析流程：从触发到放行或中断' },
  { fig: '图8-7.svg', ch: '08-路由与状态管理', sec: '08.7-Vuex核心概念',
    anchor: '## 📚 拓展阅读',
    alt: 'Vuex 五大核心的单向数据流' },
  { fig: '图8-8.svg', ch: '08-路由与状态管理', sec: '08.8-Pinia：新一代状态管理',
    anchor: '## 🧠 本节小结',
    alt: 'Pinia Setup Store 结构与 Vuex 的对比' },
  { fig: '图8-9.svg', ch: '08-路由与状态管理', sec: '08.9-Pinia模块化实战（一）：Store设计与跨Store协作',
    anchor: '## 🧠 本节小结',
    alt: 'Pinia 跨 Store 协作：购物车如何取商品价格、判断登录态' },
  { fig: '图8-10.svg', ch: '08-路由与状态管理', sec: '08.10-Pinia模块化实战（二）：购物车组件与持久化',
    anchor: '## 🧠 本节小结',
    alt: 'Pinia 购物车模块化与持久化流程' },
  { fig: '图8-11.svg', ch: '08-路由与状态管理', sec: '08.11-路由状态管理联合',
    anchor: '## 🧠 本节小结',
    alt: '路由与 Store 联合：URL 与 Store 的双向同步 + 本章知识地图' }
]

let inserted = 0
let skipped = 0
const missing = []

for (const f of FIGS) {
  const dir = path.join(BOOK, f.ch, f.sec)
  const mdPath = path.join(dir, `${f.sec}.md`)
  if (!fs.existsSync(mdPath)) { missing.push(`${f.fig} → 找不到 ${f.sec}.md`); continue }

  const svgPath = path.join(BOOK, '..', '配图', f.ch, f.fig)
  if (!fs.existsSync(svgPath)) { missing.push(`${f.fig} → 找不到配图文件`); continue }

  let md = fs.readFileSync(mdPath, 'utf-8')

  // 幂等：已引用过就跳过
  if (md.includes(f.fig)) { skipped++; continue }

  const lines = md.split('\n')
  const idx = lines.findIndex((l) => l.trim() === f.anchor)
  if (idx < 0) { missing.push(`${f.fig} → 在 ${f.sec} 里找不到锚点「${f.anchor}」`); continue }

  // 插到该标题之前
  const img = [
    '',
    `<img src="../../../配图/${f.ch}/${f.fig}" alt="${f.alt}">`,
    ''
  ]
  lines.splice(idx, 0, ...img)
  fs.writeFileSync(mdPath, lines.join('\n'))
  inserted++
  console.log(`  ✅ ${f.fig} → ${f.sec}（插在「${f.anchor.replace(/^##\s*/, '')}」前）`)
}

console.log(`\n插入 ${inserted} 张，跳过 ${skipped} 张（已引用）`)
if (missing.length) {
  console.log(`\n❌ ${missing.length} 处未处理：`)
  for (const m of missing) console.log('   ' + m)
  process.exitCode = 1
}
