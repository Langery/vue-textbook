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
    alt: '路由与 Store 联合：URL 与 Store 的双向同步 + 本章知识地图' },

  // ── 第 3 章 ──
  { fig: '图3-3.svg', ch: '03-响应式数据', sec: '03.10-ref的底层套路',
    anchor: '/^##\s*💡\s*二/', alt: 'ref 工作原理：Proxy 拦截写入并触发视图更新' },
  { fig: '图3-4.svg', ch: '03-响应式数据', sec: '03.9-不可变原则：响应式的铁律',
    anchor: '## 💡 二、reactive 的铁律：不要整体替换',
    alt: '不可变原则：改属性保持响应式，整体替换会断开 Proxy' },
  { fig: '图3-5.svg', ch: '03-响应式数据', sec: '03.7-响应式触发：为啥改了不立即变',
    anchor: '## 💡 二、Vue 的"攒一波再更新"策略',
    alt: '响应式触发：Vue 3 队列去重，同一 tick 内多次修改只渲染一次' },
  { fig: '图3-6.svg', ch: '03-响应式数据', sec: '03.8-nextTick：等DOM更新完',
    anchor: '## 💡 二、核心用法',
    alt: 'nextTick 时序：改数据后 DOM 异步更新，await nextTick 等待完成' },
  { fig: '图3-7.svg', ch: '03-响应式数据', sec: '03.3-更新对象和数组的正确姿势',
    anchor: '## 💡 二、对象更新的正确姿势',
    alt: '对象与数组的正确更新姿势：改属性、变异方法、索引赋值' },
  { fig: '图3-8.svg', ch: '03-响应式数据', sec: '03.5-reactive进阶',
    anchor: '/^##\s*🤔\s*一、/', alt: '响应式丢失的 4 个常见场景与解法' },

  // ── 第 4 章 ──
  { fig: '图4-13.svg', ch: '04-组件化思想', sec: '04.2-组件文件怎么组织',
    anchor: null, alt: 'SFC 文件的三段组织：template / script setup / style scoped' },
  { fig: '图4-14.svg', ch: '04-组件化思想', sec: '04.4-选项式vs组合式API',
    anchor: null, alt: 'defineProps 与 defineEmits：props 向下、emit 向上' },
  { fig: '图4-15.svg', ch: '04-组件化思想', sec: '04.3-组件树：看清全局',
    anchor: null, alt: '组件树的层次结构与数据流向' },
  { fig: '图4-16.svg', ch: '04-组件化思想', sec: '04.4-选项式vs组合式API',
    anchor: null, alt: '选项式 API、组合式 API 与 React 的组织方式对比' },

  // ── 第 5 章 ──
  { fig: '图5-6.svg', ch: '05-Props和事件', sec: '05.6-事件传参：emit的姿势',
    anchor: null, alt: 'defineEmits 与 $emit 传参：子触发父接收' },
  { fig: '图5-8.svg', ch: '05-Props和事件', sec: '05.7-v-model双向绑定',
    anchor: '## 💡 二、基本实现：理解 v-model 的底层机制',
    alt: 'v-model 在组件上的使用：modelValue prop 与 update:modelValue emit' },
  { fig: '图5-9.svg', ch: '05-Props和事件', sec: '05.1-Props：父子传话',
    anchor: null, alt: '父子组件通信的 4 种方式对比' },

  // ── 第 7 章 ──
  { fig: '图7-3.svg', ch: '07-组合式API与代码复用', sec: '07.2-组合式API的设计动机',
    anchor: '## 💡 二、痛点二：逻辑复用困难', alt: 'shallowRef 与 ref 的响应式范围对比' },
  { fig: '图7-4.svg', ch: '07-组合式API与代码复用', sec: '07.4-provide-inject：跨组件传数据',
    anchor: null, alt: 'readonly 防止子组件误改父级数据' },
  { fig: '图7-5.svg', ch: '07-组合式API与代码复用', sec: '07.3-computed-vs-watch-vs-methods',
    anchor: null, alt: 'computed 的缓存机制：依赖未变直接返回缓存' },
  { fig: '图7-6.svg', ch: '07-组合式API与代码复用', sec: '07.3-computed-vs-watch-vs-methods',
    anchor: null, alt: 'computed、watch、methods 的选型决策树' },
  { fig: '图7-7.svg', ch: '07-组合式API与代码复用', sec: '07.4-provide-inject：跨组件传数据',
    anchor: null, alt: 'provide/inject 跨代传数据，跳过中间层' },
  { fig: '图7-8.svg', ch: '07-组合式API与代码复用', sec: '07.5-provide-inject应用场景',
    anchor: null, alt: '用 Symbol 作为 injection key 防止命名冲突' },
  { fig: '图7-9.svg', ch: '07-组合式API与代码复用', sec: '07.6-自定义组合式函数',
    anchor: null, alt: 'Composable 的标准结构：输入 → 内部逻辑 → 返回' },
  { fig: '图7-10.svg', ch: '07-组合式API与代码复用', sec: '07.7-实用composable实战',
    anchor: null, alt: 'useDebounce 时序：连续输入只在停止后触发一次' },
  { fig: '图7-11.svg', ch: '07-组合式API与代码复用', sec: '07.7-实用composable实战',
    anchor: null, alt: 'useLocalStorage 的双向同步流程' },
  { fig: '图7-12.svg', ch: '07-组合式API与代码复用', sec: '07.8-自定义指令',
    anchor: null, alt: '自定义指令的生命周期与 binding 参数' },
  { fig: '图7-13.svg', ch: '07-组合式API与代码复用', sec: '07.8-自定义指令',
    anchor: null, alt: 'v-copy、v-focus、v-debounce 三个自定义指令用法' },
  { fig: '图7-14.svg', ch: '07-组合式API与代码复用', sec: '07.9-VueUse：瑞士军刀',
    anchor: null, alt: 'VueUse 生态总览：按分类组织的 200+ composable' },
  { fig: '图7-15.svg', ch: '07-组合式API与代码复用', sec: '07.9-VueUse：瑞士军刀',
    anchor: null, alt: 'useStorage 工作原理：ref 与 localStorage 的双向同步' },
  { fig: '图7-16.svg', ch: '07-组合式API与代码复用', sec: '07.9-VueUse：瑞士军刀',
    anchor: null, alt: 'useDark 工作原理：系统偏好到主题 Class 的切换流程' },
  { fig: '图7-17.svg', ch: '07-组合式API与代码复用', sec: '07.9-VueUse：瑞士军刀',
    anchor: null, alt: 'useClipboard 的复制流程与提示重置' },

  // ── 第 10 章 ──
  { fig: '图10-2.svg', ch: '10-表单处理与验证', sec: '10.2-表单输入绑定',
    anchor: null, alt: '五种表单输入的 v-model 绑定速查表' },
  { fig: '图10-3.svg', ch: '10-表单处理与验证', sec: '10.3-表单验证基础',
    anchor: null, alt: '手写表单验证的完整流程' },
  { fig: '图10-4.svg', ch: '10-表单处理与验证', sec: '10.4-VeeValidate入门',
    anchor: null, alt: 'VeeValidate useForm 架构：values、errors、handleSubmit 等 API' },
  { fig: '图10-5.svg', ch: '10-表单处理与验证', sec: '10.5-自定义验证规则',
    anchor: null, alt: '自定义验证规则的三种方式对比' },
  { fig: '图10-6.svg', ch: '10-表单处理与验证', sec: '10.6-表单提交与重置',
    anchor: null, alt: '表单提交状态机：idle → validating → submitting → success' },
  { fig: '图10-7.svg', ch: '10-表单处理与验证', sec: '10.7-综合实战：注册表单（一）：需求分析与项目准备',
    anchor: null, alt: '注册表单的完整交互流程' },

  // ── 第 12 章 ──
  { fig: '图12-2.svg', ch: '12-综合项目', sec: '12.2-项目搭建与目录结构',
    anchor: null, alt: '前台组件树与对应的目录结构' },
  { fig: '图12-3.svg', ch: '12-综合项目', sec: '12.3-路由设计与权限控制',
    anchor: '## 💡 二、完整路由表代码', alt: '完整数据流：请求 → Pinia → 组件' },
  { fig: '图12-4.svg', ch: '12-综合项目', sec: '12.4-前台首页：闲置列表与搜索筛选',
    anchor: null, alt: '前台首页的 computed 筛选流水线' },
  { fig: '图12-5.svg', ch: '12-综合项目', sec: '12.9-前台发布闲置（表单与图片预览）',
    anchor: null, alt: '发布闲置：表单校验与本地图片预览流程' },
  { fig: '图12-6.svg', ch: '12-综合项目', sec: '12.10-前台购物车与模拟下单',
    anchor: null, alt: '购物车跨页面状态共享：Pinia store 作为单一数据源' },
  { fig: '图12-7.svg', ch: '12-综合项目', sec: '12.12-闲置物品管理（二）：表单页与分页详解',
    anchor: '## 🔧 二、分页逻辑详解', alt: '管理后台的 CRUD 与分页数据流' },
  { fig: '图12-8.svg', ch: '12-综合项目', sec: '12.18-项目打包与部署',
    anchor: null, alt: '部署流程：vite build → dist → Nginx 静态托管' }
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
  let idx = -1

  if (f.anchor) {
    // 精确匹配优先
    idx = lines.findIndex((l) => l.trim() === f.anchor)
    // 再试正则匹配（anchor 可以写成 /正则/ 形式）
    if (idx < 0 && f.anchor.startsWith('/') && f.anchor.endsWith('/')) {
      const re = new RegExp(f.anchor.slice(1, -1))
      idx = lines.findIndex((l) => l.startsWith('## ') && re.test(l))
    }
  }

  // 兜底：插到小节内第一个实质内容标题
  //
  // ⚠️ 不要用 emoji 字符类来排除样板标题——带变体选择符（U+FE0F）的 emoji
  // 在字符类里会误匹配，结果所有带 emoji 的标题都被排除，兜底反而落到
  // 「常见陷阱」这种末尾章节。这里改为匹配**标题里的关键词**。
  if (idx < 0 && f.fallback !== false) {
    const SKIP = /(学习目标|思维导图|本节小结|本章小结|即时练习|拓展阅读|参考|答案|常见陷阱|常见误区|常见选型错误|冷知识|小灶|项目需求|分步提示|延伸挑战)/
    idx = lines.findIndex((l, i) => i > 0 && l.startsWith('## ') && !SKIP.test(l))
    if (idx < 0) { missing.push(`${f.fig} → ${f.sec} 里找不到任何可插入的标题`); continue }
  }

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
  console.log(`  ✅ ${f.fig} → ${f.sec}（插在「${lines[idx].replace(/^##\s*/, '').slice(0, 26)}」前）`)
}

console.log(`\n插入 ${inserted} 张，跳过 ${skipped} 张（已引用）`)
if (missing.length) {
  console.log(`\n❌ ${missing.length} 处未处理：`)
  for (const m of missing) console.log('   ' + m)
  process.exitCode = 1
}
