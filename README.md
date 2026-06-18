# 格物

> **格物** —— 取自「格物致知」：探究事物本质，以获得真知。
>
> 一套面向学习者的动手学习系列，核心理念：**看懂原理 -> 亲手从零实现**。

---

## 分卷地图

| 分卷 | 入口 | 内容 |
|------|------|------|
| 大模型卷 | [llm-volume/](./llm-volume/) | 从数学、PyTorch、语言模型、Transformer 到从零实现 GPT |
| Agent 卷 | [agent-volume/](./agent-volume/) | 从 single-agent harness 到 sub-agent、agent team 和 multi-agent 协同 |

## Web 可视化

Web 演武场入口：

- [web/](./web/)

运行：

```bash
cd web
npm install
npm run dev
```

当前 Web 已支持“分卷”入口结构；大模型卷的 14 卷演武场可直接使用，Agent 卷演武场后续按 `agent-volume/WEB_INTEGRATION.md` 接入。

## 项目说明

- [项目文档.md](./项目文档.md)
- [大模型卷项目入口](./llm-volume/)
- [Agent 卷项目入口](./agent-volume/)

