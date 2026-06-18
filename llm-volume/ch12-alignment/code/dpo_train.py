"""
ch12 · 示例 2:DPO —— 不要奖励模型,直接用偏好把模型「掰」过来
==================================================================
经典 RLHF 要先训奖励模型(示例 1),再用强化学习(PPO)去优化——又绕又难调。
DPO(Direct Preference Optimization,直接偏好优化)发现:这两步可以**合并成一步**。
不用训奖励模型,不用 PPO,直接拿偏好对去更新模型本身,一个简单的损失就够了。

核心直觉:
  · 我们要的无非是「让模型多说人类偏好的回答、少说不偏好的」;
  · 同时又**不能跑太偏**——不然模型会为了讨好而胡说、失去原有能力。
  · DPO 的损失天然包含这两件事:把「好回答 vs 坏回答」的概率差拉开,
    但所有概率都和一个**冻结的参考模型 ref**(就是没对齐前的自己)比较,
    系数 β 控制「能偏离 ref 多远」——这就是那条「别跑太偏」的缰绳。

为看清本质,这里把「模型」简化成:对同一个问题的 K 个候选回答的一个概率分布。
策略 policy 从参考 ref 出发,只用偏好对训练,看它怎么把概率挪向好回答。
"""
import torch
import torch.nn.functional as F

torch.manual_seed(0)

# ---------- 1. 一个问题,5 个候选回答,各有「真实质量」(我们假装不知道) ----------
RESPONSES = ["跑题的回答", "啰嗦的回答", "还行的回答", "不错的回答", "完美的回答"]
true_quality = torch.tensor([-2.0, -0.5, 0.5, 1.5, 3.0])
K = len(RESPONSES)

# 参考模型 ref:对齐前的模型。这里让它对 5 个回答几乎一视同仁(略带随机),并冻结。
ref_logits = torch.randn(K) * 0.2
ref_logp = F.log_softmax(ref_logits, dim=-1)        # 冻结不动

# 策略 policy:要训练的模型,从 ref 出发(初始就是 ref 的复制)。
policy_logits = ref_logits.clone().requires_grad_(True)

# ---------- 2. 造人类偏好对(同示例 1:质量高的更可能被选为更好) ----------
def sigmoid(z): return 1.0 / (1.0 + torch.exp(-z))
g = torch.Generator().manual_seed(1)
pairs = []
for _ in range(2000):
    i, j = torch.randperm(K, generator=g)[:2].tolist()
    if torch.rand(1, generator=g).item() < sigmoid(true_quality[i] - true_quality[j]).item():
        pairs.append((i, j))
    else:
        pairs.append((j, i))
win = torch.tensor([w for w, _ in pairs])
lose = torch.tensor([l for _, l in pairs])
print(f"收集到 {len(pairs)} 条人类偏好。开始 DPO 训练(不训奖励模型,直接更新策略)\n")

# ---------- 3. DPO 损失,直接优化 policy ----------
# 每个回答的「对齐信号」= policy 的 log 概率 - ref 的 log 概率(偏离 ref 多少)。
# DPO 损失 = -log sigmoid( β · [ 信号(赢家) - 信号(输家) ] )
# 直觉:逼着「赢家比 ref 更受青睐、输家比 ref 更被冷落」,而 β 限制总体别偏太远。
BETA = 0.5
opt = torch.optim.Adam([policy_logits], lr=0.05)
for step in range(1, 501):
    logp = F.log_softmax(policy_logits, dim=-1)
    margin_win = logp[win] - ref_logp[win]
    margin_lose = logp[lose] - ref_logp[lose]
    loss = -F.logsigmoid(BETA * (margin_win - margin_lose)).mean()
    opt.zero_grad(); loss.backward(); opt.step()
    if step == 1 or step % 100 == 0:
        print(f"  第 {step:>3} 步  loss = {loss.item():.4f}")

# ---------- 4. 对比:对齐前(ref) vs 对齐后(policy)的概率分布 ----------
ref_p = ref_logp.exp().detach()
pol_p = F.log_softmax(policy_logits, dim=-1).exp().detach()
print("\n===== 对齐前后,模型选各回答的概率 =====")
print(f"{'回答':<8}{'真实质量':>8}{'对齐前':>10}{'对齐后':>10}")
for k in torch.argsort(true_quality, descending=True).tolist():
    print(f"{RESPONSES[k]:<8}{true_quality[k].item():>+8.1f}{ref_p[k].item():>10.3f}{pol_p[k].item():>10.3f}")

best = torch.argmax(true_quality).item()
print(f"\n对齐后,概率最高的回答是「{RESPONSES[torch.argmax(pol_p).item()]}」"
      f"(真实最优是「{RESPONSES[best]}」): {torch.argmax(pol_p).item() == best}")

print("""
小结:
  · DPO 把「训奖励模型 + 跑 PPO」两步,压成了「一个损失、直接更新模型」一步。
  · 损失 = -log sigmoid(β·[(好回答相对 ref 的提升) - (坏回答相对 ref 的提升)]):
      只要偏好对,就能把概率挪向人类喜欢的回答。
  · 处处和冻结的参考模型 ref 比较,β 当缰绳:既学会偏好,又不至于跑偏失去原有能力。
  · 上面看到:对齐后,好回答的概率被明显抬高,差回答被压低,而整体仍是合法分布。
  · 真实场景里,这里的「K 个回答的概率」就是语言模型对整句回答的生成概率;
    原理一模一样,只是把分布换成了一个真正的 GPT。这就是当下最流行的对齐方法之一。
""")
