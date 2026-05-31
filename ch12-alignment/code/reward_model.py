"""
ch12 · 示例 1:RLHF 的第一步 —— 从「人类偏好」学出一个打分器(奖励模型)
========================================================================
模型会说话了(第九章),也能调风格了(第十章)。但「会说」不等于「说得好」:
它可能啰嗦、跑题、甚至胡说。怎么让它说得「有用、合人意」?这就是**对齐(alignment)**。

RLHF(基于人类反馈的强化学习)的第一步,不是直接教模型「正确答案」——
因为「好不好」太主观,很难写出标准答案。但人类**很擅长比较**:
给两个回答,说「这个比那个好」要容易得多。

于是思路是:
  1) 收集大量「偏好对」:同一个问题,A 回答 vs B 回答,人选出更好的那个;
  2) 用这些偏好,训练一个**奖励模型**:给任意回答打一个分,好的高、差的低。

本示例用最简单的形式手写这个过程:每个回答先有个「隐藏的真实质量」(模拟人心里的尺子),
人按 Bradley-Terry 模型给出偏好;我们只看偏好对,反过来把每个回答的分数学出来。
"""
import numpy as np

np.set_printoptions(precision=3, suppress=True)
rng = np.random.default_rng(0)

# ---------- 1. 造数据:5 个回答,各有一个「真实质量」(我们假装不知道) ----------
RESPONSES = ["跑题的回答", "啰嗦的回答", "还行的回答", "不错的回答", "完美的回答"]
true_quality = np.array([-2.0, -0.5, 0.5, 1.5, 3.0])   # 心里那把尺子(我们要把它学出来)
n = len(RESPONSES)

# ---------- 2. 人类给偏好:随机挑两个回答比较,按 Bradley-Terry 概率选「赢家」----------
# Bradley-Terry:回答 a 胜过 b 的概率 = sigmoid(quality_a - quality_b)。
# 质量差得越多,人越笃定;质量接近时,选择就接近抛硬币。
def sigmoid(z):
    return 1.0 / (1.0 + np.exp(-z))

pairs = []           # 每条记录:(更好的回答 idx, 更差的回答 idx)
for _ in range(2000):
    i, j = rng.choice(n, size=2, replace=False)
    p_i_wins = sigmoid(true_quality[i] - true_quality[j])
    if rng.random() < p_i_wins:
        pairs.append((i, j))     # i 赢
    else:
        pairs.append((j, i))     # j 赢
pairs = np.array(pairs)
print(f"收集到 {len(pairs)} 条人类偏好(只知道每对里谁更好,不知道具体分数)")

# ---------- 3. 训练奖励模型:为每个回答学一个分数 reward[k] ----------
# 只用偏好对当监督信号。目标:让「赢家分 - 输家分」尽量大。
# 损失 = -log sigmoid(reward[赢] - reward[输]),这正是 Bradley-Terry 的负对数似然。
reward = np.zeros(n)             # 待学习的打分器,从全 0 开始
lr = 0.1
for epoch in range(1, 401):
    win, lose = pairs[:, 0], pairs[:, 1]
    diff = reward[win] - reward[lose]
    # 损失对 diff 的梯度:-(1 - sigmoid(diff));再分发到 win(+) 和 lose(-)
    g = -(1.0 - sigmoid(diff))
    grad = np.zeros(n)
    np.add.at(grad, win, g)
    np.add.at(grad, lose, -g)
    reward -= lr * grad / len(pairs)
    if epoch == 1 or epoch % 100 == 0:
        loss = -np.log(sigmoid(diff) + 1e-12).mean()
        print(f"  第 {epoch:>3} 轮  loss = {loss:.4f}")

# ---------- 4. 看结果:学出的分数,排序对不对? ----------
reward -= reward.mean()          # 分数只有相对意义,平移到均值 0 方便对比
print("\n===== 学到的奖励 vs 真实质量 =====")
for k in np.argsort(-reward):
    print(f"  {RESPONSES[k]}:  奖励模型打分 {reward[k]:+.2f}   (真实质量 {true_quality[k]:+.1f})")

order_learned = list(np.argsort(-reward))
order_true = list(np.argsort(-true_quality))
print(f"\n奖励模型的排序是否和真实质量一致: {order_learned == order_true}")

print("""
小结:
  · 对齐的起点:人类不擅长写「标准答案」,但擅长「二选一比较」。
  · 奖励模型 = 从一堆「A 比 B 好」的偏好里,反推出一把能给任意回答打分的尺子。
  · 用的损失是 -log sigmoid(好的分 - 差的分):逼着赢家分高、输家分低。
  · 学出的分数只看相对高低就够用——它的作用是当 RLHF 里的「裁判」。
  · 经典 RLHF 下一步:拿这个奖励模型当回报,用强化学习(PPO)去推模型多说高分回答。
    但 PPO 那套又复杂又难调——所以下个示例看更简洁的替代方案 DPO。
""")
