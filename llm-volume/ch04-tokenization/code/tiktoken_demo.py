"""
ch04 · 示例 4:真实 GPT 的分词器 —— tiktoken
================================================
前面我们从零手写了 BPE。这一节直接用 OpenAI 开源的 `tiktoken`,
看看真正的 GPT 在拿什么样的分词器切你的每一句话。

它和我们手写的 BPE 是同一个思路,只是:
  · 在海量文本上合并了几万次,词表约 5 万~10 万
  · 在「字节」而非「字符」上做合并,所以任何字符都能编码,绝不 OOV

运行前先安装:  pip install tiktoken
"""

try:
    import tiktoken
except ImportError:
    print("没装 tiktoken,先运行:  pip install tiktoken")
    raise SystemExit


# GPT-2 用的是 gpt2 编码;GPT-3.5 / GPT-4 用的是 cl100k_base
enc = tiktoken.get_encoding("cl100k_base")   # GPT-3.5/4 同款
gpt2 = tiktoken.get_encoding("gpt2")          # GPT-2 同款

print(f"GPT-2  词表大小:{gpt2.n_vocab}")
print(f"GPT-4  词表大小:{enc.n_vocab}(cl100k_base)")


def show(text):
    """编码一段文字,并打印每个 token 对应的片段。"""
    ids = enc.encode(text)
    pieces = [enc.decode([i]) for i in ids]
    print(f"\n  {text!r}")
    print(f"    -> {len(ids)} 个 token:{ids}")
    print(f"    每块:{pieces}")


print("\n========== 英文:常见词整块,词缀拆开 ==========")
show("tokenization")          # token + ization
show("ChatGPT is amazing!")   # Chat + G + PT + ...

print("\n========== 空格也算进 token(GPT 的小细节) ==========")
for s in ["hello", " hello"]:
    ids = enc.encode(s)
    print(f"  {s!r:>9} -> {ids}（前导空格让它变成另一个 token)")

print("\n========== 中文:多数一字一 token,偶有合并 ==========")
show("自然语言处理")          # 自/然/语/言/处理

print("\n========== 同一句话,中文比英文更「费」token ==========")
en = "Natural language processing"
zh = "自然语言处理"
print(f"  英文 {en!r} -> {len(enc.encode(en))} 个 token")
print(f"  中文 {zh!r} -> {len(enc.encode(zh))} 个 token")
print("  -> 中文每个字几乎占一个 token,英文一个 token 能装下一截单词。")
print("     这就是为什么同样长度的中文,调 API 往往更贵、更占上下文。")

print("\n========== 字节级:任何字符都能编码,绝不 OOV ==========")
emoji = "🦙"
ids = enc.encode(emoji)
print(f"  {emoji!r} -> {len(ids)} 个 token:{ids}")
print(f"  decode 回来:{enc.decode(ids)!r}(由多个字节 token 拼出)")

# 验证:编码再解码,必须一字不差
for t in ["tokenization", "自然语言处理", "🦙 ChatGPT"]:
    assert enc.decode(enc.encode(t)) == t
print("\n✓ 所有样例 decode(encode(x)) == x")

print("""
小结:真实 GPT 的分词器 = 在海量文本上跑了几万次的 BPE + 字节级兜底。
  · 常见英文词整块保留,生僻词/词缀拆成小片;
  · 中文大多一字一 token,所以更「费」token;
  · 字节级让它能编码任何字符(emoji、生僻字),永不 OOV。
你每次和 ChatGPT 说话,第一步就是它在这样切你的文字。
""")
