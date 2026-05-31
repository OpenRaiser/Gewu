// 极简 Python 语法高亮:把一行源码切成带 class 的片段。
// 够用即可,不追求完整的 Python 词法分析。
const KEYWORDS = new Set([
  "import", "from", "as", "def", "return", "for", "in", "range",
  "if", "else", "elif", "while", "and", "or", "not", "True", "False", "None",
  "print", "lambda",
]);
const BUILTINS = new Set(["np", "torch", "softmax", "dot", "exp", "max", "sum", "array", "norm"]);

export function highlightLine(line) {
  const tokens = [];
  // 整行注释
  const commentIdx = findComment(line);
  let codePart = line, commentPart = "";
  if (commentIdx >= 0) {
    codePart = line.slice(0, commentIdx);
    commentPart = line.slice(commentIdx);
  }

  const re = /(\s+|"[^"]*"|'[^']*'|\b\d+\.?\d*\b|\b\w+\b|[^\w\s])/g;
  let m;
  while ((m = re.exec(codePart)) !== null) {
    const t = m[0];
    if (/^\s+$/.test(t)) tokens.push({ t, c: "" });
    else if (/^["']/.test(t)) tokens.push({ t, c: "tok-str" });
    else if (/^\d/.test(t)) tokens.push({ t, c: "tok-num" });
    else if (KEYWORDS.has(t)) tokens.push({ t, c: "tok-kw" });
    else if (BUILTINS.has(t)) tokens.push({ t, c: "tok-fn" });
    else if (/^[^\w\s]$/.test(t)) tokens.push({ t, c: "tok-op" });
    else tokens.push({ t, c: "" });
  }
  if (commentPart) tokens.push({ t: commentPart, c: "tok-com" });
  return tokens;
}

function findComment(line) {
  let inStr = null;
  for (let i = 0; i < line.length; i++) {
    const ch = line[i];
    if (inStr) {
      if (ch === inStr) inStr = null;
    } else if (ch === '"' || ch === "'") {
      inStr = ch;
    } else if (ch === "#") {
      return i;
    }
  }
  return -1;
}
