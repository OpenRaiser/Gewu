"""
ch14 · 示例 2:最小 Agent 循环 —— 让模型自己调用工具、分步解决问题
====================================================================
RAG(示例 1)让模型「会查资料」。但有些任务光查资料不够,需要**动手**:
算一道数学题、查实时天气、调一个 API…… 模型本身只会生成文字,它不会算术、也连不上网。

Agent(智能体)的主意:给模型配几样**工具**,让它在一个循环里自己决定
「下一步该用哪个工具、传什么参数」,看到工具返回的结果后,再决定下一步,直到能给出最终答案。

这套循环常被称为 **ReAct**(Reason + Act,边想边做):
  想(Thought) -> 做(Action:调用某工具)-> 看(Observation:工具返回)-> 再想…… -> 最终答案

真实 Agent 里,「下一步干啥」是 GPT 生成的。这里为了把循环本身看清楚、且稳定可复现,
用一个**规则版「大脑」**代替 GPT 做决策(真实场景换成模型即可)。重点是这套
「想-做-看」的循环骨架,以及工具是怎么被调用、结果怎么回流的。
"""
import re

# ---------- 1. 工具箱:模型本身不会做的事,交给工具 ----------
def tool_calculator(expr):
    """一个安全的小算术器:只认数字和 + - * / ( )。"""
    if not re.fullmatch(r"[\d\.\s\+\-\*\/\(\)]+", expr):
        return "错误:表达式含非法字符"
    try:
        return str(eval(expr, {"__builtins__": {}}, {}))   # 受限 eval,禁掉内建
    except Exception as e:
        return f"错误:{e}"

KNOWLEDGE = {"北京人口": "约 2184 万", "光速": "约 30 万公里每秒"}
def tool_lookup(key):
    """一个小知识库查询工具。"""
    return KNOWLEDGE.get(key.strip(), "未找到")

TOOLS = {"calculator": tool_calculator, "lookup": tool_lookup}

# ---------- 2. 「大脑」:决定下一步动作。真实里这是 GPT,这里用规则模拟 ----------
def brain(question, history):
    """看问题和已有观察,返回下一步:要么 ('action', 工具名, 参数),要么 ('final', 答案)。"""
    observations = [h for h in history if h[0] == "observation"]
    if "人口" in question and "倍" in question:
        # 任务:北京人口的若干倍是多少 —— 需要先查人口,再算乘法(两步、两个工具)
        if len(observations) == 0:
            return ("action", "lookup", "北京人口")             # 第一步:查人口
        if len(observations) == 1:
            num = re.search(r"(\d+)", observations[0][1]).group(1)   # 从「约 2184 万」抠出 2184
            mult = re.search(r"(\d+)\s*倍", question).group(1)        # 从问题里抠出倍数
            return ("action", "calculator", f"{num} * {mult}")  # 第二步:算乘法
        return ("final", f"北京人口{observations[0][1]},其 {mult_str(question)} 倍约为 "
                         f"{observations[1][1]} 万")
    if "等于多少" in question:
        expr = re.search(r"([\d\.\s\+\-\*\/\(\)]+?)\s*等于多少", question)
        expr = expr.group(1).strip() if expr else question
        if len(observations) == 0:
            return ("action", "calculator", expr)
        return ("final", f"答案是 {observations[0][1]}")
    return ("final", "我暂时无法回答这个问题")


def mult_str(question):
    return re.search(r"(\d+)\s*倍", question).group(1)

# ---------- 3. Agent 循环:想 -> 做 -> 看 -> 再想…… ----------
def run_agent(question, max_steps=5):
    print(f"【问题】{question}")
    history = []
    for step in range(1, max_steps + 1):
        decision = brain(question, history)
        if decision[0] == "final":
            print(f"  第{step}步 · 最终答案:{decision[1]}\n")
            return decision[1]
        _, tool, arg = decision
        print(f"  第{step}步 · 想:该用工具 [{tool}]，参数「{arg}」")
        result = TOOLS[tool](arg)                       # 做:真的调用工具
        print(f"          · 看:工具返回「{result}」")
        history.append(("observation", result))         # 结果回流,供下一轮决策
    return "(超过最大步数)"

# ---------- 跑几个任务 ----------
run_agent("(12 + 8) * 3 等于多少?")
run_agent("北京人口的 2 倍大概是多少万?")

print("""
小结:
  · Agent = 给模型配工具,让它在「想-做-看」的循环里自己分步解决问题(ReAct 范式)。
  · 模型只会生成文字,算术、查库、调 API 这些它干不了的事,统统交给工具。
  · 循环骨架:大脑决定下一步动作 -> 调用工具 -> 把结果(观察)喂回去 -> 再决定…… 直到给出最终答案。
  · 第二个例子里,Agent 先「查」到人口、再「算」乘法——多步、多工具协作,这是单次问答做不到的。
  · 真实里这个「大脑」就是 GPT(本例用规则模拟以便复现);工具可以是搜索、代码执行、数据库……
    这就是 ChatGPT 的插件/函数调用、以及各类「AI 助手能帮你订票查天气」背后的基本范式。
""")
