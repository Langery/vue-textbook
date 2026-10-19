# 第 7 章 组合式API与代码复用 ⭐

> 课时：8.5 课时（重点章）
> 难度：⭐⭐⭐（进阶）
> 重要性：⭐⭐⭐⭐⭐（**下篇最核心**）

---

## 🎯 本章目标

学完这章，你将能够：

- ✅ 深入理解 **组合式 API（Composition API）** 的设计动机
- ✅ 熟练使用 **`ref` 进阶**（复杂对象、数组）
- ✅ 熟练使用 **`reactive`** 处理对象/数组
- ✅ 掌握 **`computed`** 计算属性（含 setter）
- ✅ 区分 **`computed` vs `methods` vs `watch`**
- ✅ 掌握 **`provide` / `inject`** 跨层级传数据
- ✅ 理解 **自定义 composable** 的设计思想
- ✅ 写出**实用 composable**（防抖、持久化、鼠标追踪）
- ✅ 掌握**自定义指令**（v-copy、v-focus、v-debounce）
- ✅ 熟练使用 **VueUse**（useStorage、useDark、useClipboard 等常用 composable）

---

## 🤔 为什么本章是下篇最核心

**前面学的（1-7 章）**还停留在"语法能用"——但代码组织还是"按选项分类"（data 在一起、methods 在一起）。

**本章教你"按逻辑组合"**——把一个功能的代码（ref + computed + method）写在一起，可复用、可测试。这是从"会用 Vue"到"会用 Vue 写工程"的**第二次分水岭**。

> 🧑 **小白**：我按 data、methods、computed 分门别类写，已经挺整齐了，为啥还要学组合式 API？

> 🤖 **Vue 君**：因为"整齐"是按代码类型排的，可你要维护的是一个"功能"——它的数据、方法、计算属性常常散落在三个区块里，改一处得来回翻。

> 👨🏫 **老湿**：组合式 API 让你按"功能"把代码聚成一团，还能抽成 composable 复用。这是下篇最核心的一章。

> 💬 **老师备注**：本章是下篇**最关键的一章**。如果只学一章，必须是这一章 + 第 8 章。

---

## 📋 本章小节

| 节 | 标题 | 课时 |
|---|---|---|
| 07.1 | 组合式API是啥 | 0.5 |
| 07.2 | 组合式API的设计动机 | 0.5 |
| 07.3 | computed-vs-watch-vs-methods | 0.5 |
| 07.4 | provide-inject：跨组件传数据 | 0.5 |
| 07.5 | provide-inject应用场景 | 0.5 |
| 07.6 | 自定义组合式函数 | 0.5 |
| 07.7 | 实用composable实战 | 1 |
| 07.8 | 自定义指令 | 1 |
| 07.9 | VueUse：瑞士军刀 | 1 |
| 07.10 | effectScope | 1 |
| 07.11 | 本章小测 | 0.5 |
| 07.12 | 本地笔记 | 1 |
| **合计** | **12 节** | **8.5** |
| 7.2 | 组合式 API 的设计动机 | 解决选项式痛点、对比 Mixin | 0.5 |
| 7.3 | computed vs watch vs methods | 三种 API 对比、选型指南 | 0.5 |
| 7.4 | `provide` / `inject`：跨组件传数据 | 隔代传、readonly 防误改 | 0.5 |
| 7.5 | `provide` / `inject` 应用场景 | 主题、表单、面包屑、权限 | 0.5 |
| 7.6 | 自定义组合式函数（Composables） | 命名规范、结构模板、返回值设计 | 0.5 |
| **7.7** | **实用 composable 实战** ⭐ | useDebounce、useLocalStorage、useMouse + VueUse | **1** |
| **7.8** | **自定义指令** ⭐ | v-copy、v-focus、v-debounce、简写形式 | **1** |
| **7.9** | **VueUse 生态：瑞士军刀** ⭐⭐ | useStorage/useDark/useClipboard + 200+ composable | **1** |
| **7.10** | **`effectScope`：批量管理副作用** ⭐⭐ | 批量管理副作用、自定义 composable 基石 | **1** |
| 7.11 | 本章小测 | 6 选择 + 5 判断 + 3 简答 + 2 编程 | 0.5 |
| **7.12** | **章末实战：本地笔记（P7）** ⭐ | 本地笔记：自动保存 + 搜索防抖 + 删除确认，全程手写 composable | **1** |

---

## 🛠 本章实战

1. 用 `computed` 实现一个**购物车总价**（自动响应商品列表变化）
2. 用 `provide` / `inject` + `readonly` 实现**主题切换**功能
3. 写 **useDebounce** 防抖 composable，配合搜索框使用
4. 写 **useLocalStorage** 持久化 composable，记住用户偏好
5. 写 **v-copy** 自定义指令，一键复制文本到剪贴板
6. 用 `v-focus` 和 `v-debounce` 指令优化表单体验
7. 用 `useDark` + `useToggle` 三行代码实现暗黑模式
8. 用 `useClipboard` 实现一键复制，复制后显示提示

---

## 📚 本章配图（规划 17 张 / 已完成 2 张）

| 图号 | 主题 | 状态 |
|---|---|---|
| 7-1 | 组合式 API vs 选项式 API 对比 | 已完成 |
| 7-2 | Mixin vs Composable 复用对比 | 已完成 |
| 7-3 | shallowRef vs ref 响应式范围 | 待做 |
| 7-4 | readonly 防子组件误改 | 待做 |
| 7-5 | computed 缓存机制 | 待做 |
| 7-6 | computed vs watch vs methods 决策图 | 待做 |
| 7-7 | provide/inject 数据流 | 待做 |
| 7-8 | Symbol Key 防命名冲突 | 待做 |
| 7-9 | Composable 结构模板 | 待做 |
| 7-10 | useDebounce 时序图 | 待做 |
| 7-11 | useLocalStorage 同步流程 | 待做 |
| 7-12 | 自定义指令生命周期 | 待做 |
| 7-13 | v-copy / v-focus / v-debounce 用法总览 | 待做 |
| 7-14 | VueUse 生态总览（200+ composable 分类） | 待做 |
| 7-15 | useStorage 工作原理（ref ↔ localStorage） | 待做 |
| 7-16 | useDark 工作原理（系统偏好 → Class → Tailwind） | 待做 |
| 7-17 | useClipboard 流程 | 待做 |

---

## ⚠️ 学习提示

- **不要背**所有 API——组合式 API 的核心是"按需 import"
- **多写自定义 composable**——这是 Vue 3 最有特色的部分
- **`computed` 不要写复杂逻辑**——超过 5 行就应该拆成函数
- **VueUse 是加速器**：遇到"这个功能有没有现成的？"先去 [vueuse.org](https://vueuse.org/) 搜一下

---

## 🔗 与其他章的关系

- **前置**：第 4 章（组件化）+ 第 3 章（响应式）
- **后续直接被依赖**：第 8 章（路由与状态管理）、第 11 章（测试与调试）

## 📖 本章术语表

下表收录本章 7.1~7.12 正文实际讲到的核心术语，按首次出现的节号排序，方便随时回查。

| 术语 | 一句话解释 | 首现节号 |
|---|---|---|
| `组合式 API` | Vue 3 主推的组织代码方式，把同一功能的数据、方法、监听等写在 setup 中聚合。 | 7.1 |
| `选项式 API` | Vue 2 传统写法，按 data、methods、computed、watch 等类型分块组织组件代码。 | 7.1 |
| `<script setup>` | 组合式 API 的语法糖写法，在单文件组件中直接写逻辑，无需 export default 选项。 | 7.1 |
| `Mixin` | Vue 2 时代复用逻辑的混入机制，存在命名冲突、来源不透明、隐式耦合等问题。 | 7.2 |
| `composable` | 以 use 开头、封装独立功能并返回响应式状态与方法的组合式函数，如 useMouse。 | 7.2 |
| `命名冲突` | 多个 Mixin 或来源的同名属性互相覆盖、难以排查的问题，composable 通过显式解构规避。 | 7.2 |
| `provide` | 祖先组件向所有后代注入数据的 API，配合 inject 实现隔代传值、跳过中间层。 | 7.4 |
| `inject` | 后代组件获取祖先 provide 数据的 API，按 key 读取注入值，可选默认值。 | 7.4 |
| `Prop Drilling` | 中间层组件被迫逐级转发不关心的 Props 的传值现象，可用 provide/inject 消除。 | 7.4 |
| `readonly` | 把对象包装为只读的 API，常用于 provide 传值防止子组件误改共享数据。 | 7.4 |
| `Symbol` | 用 Symbol 作为 provide/inject 的 key，可避免字符串 key 的命名冲突问题。 | 7.5 |
| `useXxx 约定` | composable 的命名规范：函数以 use 开头、大写名词结尾，如 useMouse、useFetch。 | 7.6 |
| `防抖` | 多次触发只执行最后一次的技术，常用于搜索输入，减少无效请求、提升性能。 | 7.7 |
| `useDebounce` | 封装防抖逻辑的 composable，监听源值变化延迟更新，返回防抖后的 ref。 | 7.7 |
| `useLocalStorage` | 让 ref 与 localStorage 双向同步的 composable，刷新页面后数据依然保留。 | 7.7 |
| `自定义指令` | 用 v-xxx 声明式给元素挂载 DOM 行为的复用机制，如 v-copy、v-focus、v-debounce。 | 7.8 |
| `VueUse` | Vue 官方团队维护的 composable 工具库，提供 200+ 个开箱即用的组合式函数。 | 7.9 |
| `useStorage` | VueUse 提供的响应式 localStorage 封装，一行代码实现持久化读写与多 Tab 同步。 | 7.9 |
| `effectScope` | 批量管理副作用的"作用域容器"，域内所有 watcher/computed 可经 stop() 一次停掉。 | 7.10 |
| `onScopeDispose` | 在 effectScope 内注册清理函数的 API，作用域停止时统一执行回收逻辑。 | 7.10 |

---

**（开始学习：7.1 组合式 API 是啥 →）**
