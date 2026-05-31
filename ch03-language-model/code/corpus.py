"""
ch03 · 共享语料与工具
=====================
语料:一批中文名字。语言模型的任务,就是看着前面的字、猜下一个字。
我们用名字做例子——既直观,生成出来的"新名字"也好玩。

边界符 "·" 同时表示「开头」和「结尾」:
  ·天明·  ->  (·->天), (天->明), (明->·)
这样模型既能学会"名字以什么字开头",也能学会"何时该收尾"。
"""

# 语料:常见名字(纯属示例,非指向真实个人)
NAMES = [
    "天明", "天宇", "天佑", "天华",
    "小龙", "小川", "小雨", "小满", "晓彤",
    "春华", "春燕", "春明", "志强", "志明", "志华",
    "建国", "建华", "建明", "国华", "国强", "国栋",
    "云飞", "云龙", "云帆", "海燕", "海涛", "海明",
    "明华", "明远", "明轩", "文华", "文轩", "文静",
    "雨桐", "雨欣", "梓涵", "梓轩", "子轩", "宇轩",
    "嘉文", "嘉豪", "佳怡", "思远", "思齐",
]

TOKEN = "·"   # 开头/结尾的边界符


def build_vocab(names=NAMES):
    """收集所有出现过的字,建立「字 <-> 编号」双向映射。"""
    chars = set(TOKEN)
    for nm in names:
        chars.update(nm)
    vocab = sorted(chars)
    stoi = {c: i for i, c in enumerate(vocab)}   # 字 -> 编号
    itos = {i: c for c, i in stoi.items()}       # 编号 -> 字
    return vocab, stoi, itos


def bigrams(name):
    """把一个名字拆成相邻字对:'天明' -> (·,天),(天,明),(明,·)"""
    chs = [TOKEN] + list(name) + [TOKEN]
    return list(zip(chs, chs[1:]))


if __name__ == "__main__":
    vocab, stoi, itos = build_vocab()
    print("语料共", len(NAMES), "个名字")
    print("不同的字(含边界符)共", len(vocab), "个:")
    print("".join(vocab))
    print("\n示例拆分 '天明' ->", bigrams("天明"))
