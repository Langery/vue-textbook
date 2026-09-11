# 第 8 章 组合式 API 精讲 ⭐

> 课时：9 课时（重点章）
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

> 💬 **老师备注**：本章是下篇**最关键的一章**。如果只学一章，必须是这一章 + 第 9 章。

---

## 📋 本章小节

| 节 | 标题 | 内容 | 课时 |
|---|---|---|---|
| 8.1 | 组合式 API 是啥 | `setup` 函数、`<script setup>` | 0.5 |
| 8.2 | 组合式 API 的设计动机 | 解决选项式痛点、对比 Mixin | 0.5 |
| 8.3 | `ref` 进阶：复杂状态 | shallowRef、triggerRef、toRef | 0.5 |
| 8.4 | `reactive` 进阶 | readonly、shallowReactive、markRaw | 0.5 |
| 8.5 | `computed`：派生状态 | 缓存机制、可写计算属性 | 0.5 |
| 8.6 | `computed` vs `methods` vs `watch` | 三种 API 对比、选型指南 | 0.5 |
| 8.7 | `provide` / `inject`：跨组件传数据 | 隔代传、readonly 防误改 | 0.5 |
| 8.8 | `provide` / `inject` 应用场景 | 主题、表单、面包屑、权限 | 0.5 |
| 8.9 | 自定义 composable 设计模式 | 命名规范、结构模板、返回值设计 | 0.5 |
| **8.10** | **实用 composable 实战** ⭐ | useDebounce、useLocalStorage、useMouse + VueUse | **1** |
| **8.11** | **自定义指令** ⭐ | v-copy、v-focus、v-debounce、简写形式 | **1** |
| **8.12** | **VueUse 生态：瑞士军刀** ⭐⭐ | useStorage/useDark/useClipboard + 200+ composable | **1** |
| 8.13 | 本章小测 | 6 选择 + 5 判断 + 3 简答 + 2 编程 | 0.5 |
| **8.14** | **章末实战：本地笔记** ⭐ | 本地笔记：自动保存 + 搜索防抖 + 删除确认，全程手写 composable | **1** |

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

## 📚 本章配图（17 张）

| 图号 | 主题 | 状态 |
|---|---|---|
| 8-1 | 组合式 API vs 选项式 API 对比 | 待做 |
| 8-2 | Mixin vs Composable 复用对比 | 待做 |
| 8-3 | shallowRef vs ref 响应式范围 | 待做 |
| 8-4 | readonly 防子组件误改 | 待做 |
| 8-5 | computed 缓存机制 | 待做 |
| 8-6 | computed vs watch vs methods 决策图 | 待做 |
| 8-7 | provide/inject 数据流 | 待做 |
| 8-8 | Symbol Key 防命名冲突 | 待做 |
| 8-9 | Composable 结构模板 | 待做 |
| 8-10 | useDebounce 时序图 | 待做 |
| 8-11 | useLocalStorage 同步流程 | 待做 |
| 8-12 | 自定义指令生命周期 | 待做 |
| 8-13 | v-copy / v-focus / v-debounce 用法总览 | 待做 |
| 8-14 | VueUse 生态总览（200+ composable 分类） | 待做 |
| 8-15 | useStorage 工作原理（ref ↔ localStorage） | 待做 |
| 8-16 | useDark 工作原理（系统偏好 → Class → Tailwind） | 待做 |
| 8-17 | useClipboard 流程 | 待做 |

---

## ⚠️ 学习提示

- **不要背**所有 API——组合式 API 的核心是"按需 import"
- **多写自定义 composable**——这是 Vue 3 最有特色的部分
- **`computed` 不要写复杂逻辑**——超过 5 行就应该拆成函数
- **VueUse 是加速器**：遇到"这个功能有没有现成的？"先去 [vueuse.org](https://vueuse.org/) 搜一下

---

## 🔗 与其他章的关系

- **前置**：第 3 章（组件化）+ 第 5 章（响应式）
- **后续直接被依赖**：第 9 章（路由与状态管理）、第 12 章（测试与调试）

---

**（开始学习：8.1 组合式 API 是啥 →）**
