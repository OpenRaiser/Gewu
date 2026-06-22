# Sub-Agent Runner 实验

这个实验用于 ch05：演示最小 manager-worker / sub-agent 结构。

它不调用真实模型，而是用确定性 worker 展示 sub-agent harness 的关键形态：

```text
manager
  -> worker-roadmap reads only roadmap.md
  -> worker-ch05 reads only ch05 README
  -> aggregate reports
  -> write result.json
```

## 运行

```bash
cd agent-volume/experiments/sub-agent-runner
python3 manager.py --reset
```

查看输出：

```bash
find run -maxdepth 2 -type f | sort
cat run/result.json
```

## 输出文件

```text
run/
  manager.jsonl
  worker-roadmap.jsonl
  worker-ch05.jsonl
  result.json
```

## 观察重点

- manager 只分派任务和聚合，不直接读所有细节
- 每个 worker 有自己的 trace
- worker report 是摘要，不是完整 trace
- result.json 是 reducer 的聚合结果

