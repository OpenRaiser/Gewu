# Web 演武场改造待办

目标：把现有 Web 演示从“独立概念海报”升级为“从零搭 GPT 的连续可视化实验室”。改造重点不是单纯加长代码，而是让每一章都能看见变量从哪里来、在内部如何变化、又流向下一章哪里。

## 总体原则

- 每个 demo 必须说明：前置概念、当前核心变量、下一步承接、对应 Python 来源。
- 核心章节优先展示内部状态，而不是只展示结论图。
- Python 示例应逐步成为 Web 数据来源，避免手工搬运实测数字。
- UI 保持当前古籍风格，但信息结构要更像调试器：变量表、矩阵、形状、流程、代码同步高亮。

## P0：主线修复

- [x] 创建本待办文档。
- [x] 给 demo 契约增加可选承接元数据：`bridge.prev`、`bridge.current`、`bridge.next`、`bridge.sources`。
- [x] 在 `Codex` 中展示承接元数据，形成“承前 / 本式 / 启后 / 来源”固定区域。
- [x] 去掉“运行真身 / 演法真身”按钮与 Pyodide 执行入口，只保留“演法”推导体验。
- [x] 抽出通用矩阵热力图组件，用于 attention、mask、logits、相似度等可视化。
- [x] 重做 ch06 第一式：展示 `X @ X.T` 分数矩阵、当前行、softmax 权重、加权汇总。
- [x] 加深 ch06 第一式：把 `C[j]=w[j]*X[j]` 和 `y=C[0]+...` 在演武场中逐词、逐维展开。
- [x] 重做 ch06 第二式：展示 `Q/K/V` 投影、`QK.T / sqrt(d)` 矩阵、权重行、`weights @ V`。
- [x] 加深 ch06 第二式：把 `Q = X @ Wq.T`、`K = X @ Wk.T`、`V = X @ Wv.T` 展开成行级点积。
- [x] 重做 ch06 第三式：修复当前 `p.qi` 取值错误，并展示 mask 前分数、mask 后分数、softmax 后权重。
- [x] 运行 `npm run build` 验证前端构建。
- [x] 启动本地 Web 并用浏览器检查 ch06 三个 demo 的视觉效果。

## P1：GPT 主干章节

- [ ] ch07 补完整 Transformer Block 状态：Attention、Residual、LayerNorm、FFN、Residual。
- [ ] ch08 改成逐层 shape trace：`idx -> tok_emb -> pos_emb -> blocks -> logits -> loss`。
- [ ] ch09 展示 batch 构造、右移标签、逐位置 loss、梯度更新、生成样例变化。
- [ ] 为 ch08/ch09 从 Python 导出 JSON trace，Web 只负责展示。

## P2：语言模型前置主线

- [ ] ch01 每个数学 demo 增加“后续使用位置”：点积、矩阵乘、softmax、梯度分别连到 attention/training。
- [ ] ch03 串联 “语料 -> bigram 计数 -> 概率表 -> 生成 -> loss”。
- [ ] ch04 在同一句样本上对比 char / word / BPE / tiktoken 的 token 数和失败模式。
- [ ] ch05 串联 “ID -> one-hot -> embedding lookup -> cosine -> learned embedding”。

## P3：模型变好用

- [ ] ch10 展示 logits、temperature、top-k、top-p 对候选集和熵的影响。
- [ ] ch11 增加真实 LoRA 训练曲线，展示冻结参数与可训练旁路。
- [ ] ch12 对照 RLHF 奖励模型与 DPO：偏好对如何改变回答分布。

## P4：工程与应用

- [ ] ch13 KV cache 展示 K/V 张量随 token 增长；量化展示误差、outlier、反量化。
- [ ] ch14 RAG 增加检索失败案例、prompt 拼接、引用来源。
- [ ] ch14 Agent 增加工具 schema、历史状态、错误重试、终止判断。

## P5：维护质量

- [ ] 建立 `web/src/demos/data/`，由 Python 脚本导出关键 trace JSON。
- [ ] 给每个 demo 标注 `sourceFiles` 并在构建前检查文件存在。
- [ ] 增加轻量 Playwright smoke：打开页面、切到关键卷、确认 SVG 非空且无控制台错误。
- [ ] 清理或忽略根目录和子目录中的 `._*` AppleDouble 元数据文件。
