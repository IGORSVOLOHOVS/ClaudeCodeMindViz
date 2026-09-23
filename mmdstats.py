#!/usr/bin/env python3
"""mmdstats — статистика по Mermaid-графу решений.

Читает flowchart из .md (первый блок ```mermaid) или .mmd и печатает:
счётчики узлов по типу (Q/H/T/A) и статусу (active/done/rejected),
открытые вопросы, отвергнутые гипотезы и самую длинную цепочку.

Использование:
  python mmdstats.py [файл] [--json]
Файл по умолчанию: .claude/decision_graph/current_task.md

Разбор построчный: узлы `id["текст"]:::статус` в любой фигуре Mermaid
([ ], ( ), ([ ]), {{ }}, > ], [/ /], без кавычек), рёбра -->, ---, -.->, ==>,
<-->, --o, цепочки A --> B --> C, группы A & B --> C, подписи |"..."| и
-- текст -->, операторы `class A,B статус`. Строка, которую не удалось
разобрать, печатается в stderr и пропускается.
Самая длинная цепочка идёт только по неотвергнутым узлам.
"""
import argparse
import collections
import html
import json
import pathlib
import re
import sys

DEFAULT_FILE = pathlib.Path(".claude/decision_graph/current_task.md")
KINDS = {"Q": "вопрос", "H": "гипотеза", "T": "проверка", "A": "решение"}
STATUSES = ("active", "done", "rejected")
BRUTE_FORCE_LIMIT = 300  # выше — перебор простых путей в циклическом графе не запускаем

FENCE = re.compile(r"```mermaid[^\n]*\n([\s\S]*?)(?:```|$)")
HEADER = re.compile(r"^(flowchart|graph)\b")
SKIP = re.compile(r"^(?:%%|flowchart\b|graph\b|classDef\b|style\b|linkStyle\b|subgraph\b|end\b|direction\b|click\b|accTitle\b|accDescr\b)")
CLASS_STMT = re.compile(r"^class\s+([\w,\s]+?)\s+(\w+)$")
# Узел: id, затем необязательная фигура (любые скобки) с текстом в кавычках или без, затем :::статус
NODE_DEF = re.compile(r'^(\w+)\s*(?:([\[({>/\\]+)\s*(?:"([^"]*)"|([^\]})/\\]*?))\s*[\])}/\\]+)?(?::::(\w+))?$')
QUOTED = re.compile(r'"[^"]*"')
PLACEHOLDER = re.compile(r'"\x00(\d+)\x00"')
# Подписи рёбер: |текст| убираем, «-- текст -->», «== текст ==>», «-. текст .->» сводим к голой стрелке
EDGE_LABELS = [(re.compile(r"\|[^|]*\|"), ""), (re.compile(r"--\s[^-]+?\s-->"), "-->"),
               (re.compile(r"==\s[^=]+?\s==>"), "==>"), (re.compile(r"-\.\s[^.]+?\s\.->"), "-.->")]
ARROW = re.compile(r"\s*(?:<?-{2,}>|-{3,}|-\.+->|-\.-|<?=+>|={3,}|--[ox]|~~~)\s*")


def mermaid_source(text, path=""):
    """Первый блок ```mermaid из Markdown, либо весь текст (для .mmd); проверяет, что это flowchart."""
    m = FENCE.search(text)
    if m:
        src = m.group(1)
    elif str(path).lower().endswith(".md"):
        raise ValueError("нет блока ```mermaid")
    else:
        src = text
    first = next((l.strip() for l in src.splitlines() if l.strip() and not l.strip().startswith("%%")), "")
    if not HEADER.match(first):
        raise ValueError(f"не flowchart (первая строка: {first[:40]!r})")
    return src


def _new_node(nid):
    return {"id": nid, "label": nid, "status": ""}


def _parse_line(line):
    """-> список групп узлов [[(id, opener, quoted, unquoted, status), ...], ...] или None."""
    quoted = []
    hidden = QUOTED.sub(lambda q: (quoted.append(q.group(0)), f'"\x00{len(quoted) - 1}\x00"')[1], line)
    for rx, repl in EDGE_LABELS:
        hidden = rx.sub(repl, hidden)
    groups = []
    for seg in ARROW.split(hidden):
        ids = []
        for part in seg.split("&"):
            part = PLACEHOLDER.sub(lambda p: quoted[int(p.group(1))], part.strip())
            m = NODE_DEF.match(part)
            if not m:
                return None
            ids.append(m.groups())
        groups.append(ids)
    return groups


def parse(text, path="", warn=None):
    """-> (nodes: {id: {id, label, status, kind}}, edges: [(from, to)]). warn(строка) — для нераспознанных строк."""
    nodes, edges = {}, []
    for raw in mermaid_source(text, path).splitlines():
        line = raw.strip().rstrip(";").strip()
        if not line or SKIP.match(line):
            continue
        m = CLASS_STMT.match(line)
        if m:
            for nid in m.group(1).replace(",", " ").split():
                nodes.setdefault(nid, _new_node(nid))["status"] = m.group(2)
            continue
        groups = _parse_line(line)
        if not groups:
            if warn:
                warn(raw.strip())
            continue
        prev = []
        for ids in groups:
            cur = []
            for nid, opener, qlabel, ulabel, status in ids:
                node = nodes.setdefault(nid, _new_node(nid))
                if opener:
                    label = qlabel if qlabel is not None else (ulabel or "").strip()
                    node["label"] = html.unescape(re.sub(r"#(\w+);", r"&\1;", label))  # #quot; -> "
                if status:
                    node["status"] = status
                cur.append(nid)
            edges.extend((a, b) for a in prev for b in cur)
            prev = cur
    for node in nodes.values():
        m = re.match(r"([QHTA]):", node["label"])
        node["kind"] = m.group(1) if m else "-"
    return nodes, edges


def longest_chain(nodes, edges):
    """Самый длинный путь по неотвергнутым узлам (по числу узлов).

    Ациклический граф: динамика по топологическому порядку — без рекурсии, тянет
    тысячи узлов. С циклами: перебор простых путей (такие графы маленькие);
    выше BRUTE_FORCE_LIMIT узлов — рёбра назад по порядку объявления отбрасываются.
    """
    live = [n for n, v in nodes.items() if v["status"] != "rejected"]
    out = {n: [] for n in live}
    for a, b in edges:
        if a in out and b in out and a != b and b not in out[a]:
            out[a].append(b)
    order = _topo_order(live, out)
    if order is None and len(live) > BRUTE_FORCE_LIMIT:
        pos = {n: i for i, n in enumerate(live)}
        out = {n: [m for m in ms if pos[m] > pos[n]] for n, ms in out.items()}
        order = _topo_order(live, out)
    if order is not None:
        best_len, best_next = {}, {}
        for n in reversed(order):
            best_len[n], best_next[n] = 1, None
            for m in out[n]:
                if best_len[m] + 1 > best_len[n]:
                    best_len[n], best_next[n] = best_len[m] + 1, m
        chain, n = [], (max(order, key=lambda x: best_len[x]) if order else None)
        while n is not None:
            chain.append(n)
            n = best_next[n]
    else:
        chain = []
        for start in live:
            stack = [(start, [start])]
            while stack:
                n, path = stack.pop()
                if len(path) > len(chain):
                    chain = path
                stack.extend((m, path + [m]) for m in out[n] if m not in path)
    return [nodes[n]["label"] for n in chain]


def _topo_order(live, out):
    """Порядок Кана или None, если есть цикл."""
    indeg = {n: 0 for n in live}
    for ms in out.values():
        for m in ms:
            indeg[m] += 1
    queue = collections.deque(n for n in live if indeg[n] == 0)
    order = []
    while queue:
        n = queue.popleft()
        order.append(n)
        for m in out[n]:
            indeg[m] -= 1
            if indeg[m] == 0:
                queue.append(m)
    return order if len(order) == len(live) else None


def stats(text, path="", warn=None):
    nodes, edges = parse(text, path, warn)
    by_kind = {k: {"active": 0, "done": 0, "rejected": 0, "none": 0} for k in list(KINDS) + ["-"]}
    for n in nodes.values():
        by_kind[n["kind"]][n["status"] if n["status"] in STATUSES else "none"] += 1
    return {
        "nodes": len(nodes),
        "edges": len(edges),
        "by_kind": by_kind,
        "open_questions": [n["label"] for n in nodes.values() if n["kind"] == "Q" and n["status"] == "active"],
        "rejected": [n["label"] for n in nodes.values() if n["status"] == "rejected"],
        "longest_chain": longest_chain(nodes, edges),
    }


def render(s):
    lines = [f"Узлов: {s['nodes']}, рёбер: {s['edges']}", ""]
    for kind, name in list(KINDS.items()) + [("-", "прочие")]:
        c = s["by_kind"][kind]
        total = sum(c.values())
        if total:
            lines.append(f"{name:9} {total:3}   в работе {c['active']}, принято {c['done']}, "
                         f"отвергнуто {c['rejected']}, без статуса {c['none']}")
    lines += ["", "Открытые вопросы:"] + ([f"  • {q}" for q in s["open_questions"]] or ["  — нет"])
    lines += ["", "Отвергнуто:"] + ([f"  ✗ {r}" for r in s["rejected"]] or ["  — ничего"])
    lines += ["", f"Самая длинная цепочка ({len(s['longest_chain'])}):"] + [f"  {i + 1}. {l}" for i, l in enumerate(s["longest_chain"])]
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Статистика по Mermaid-графу решений")
    ap.add_argument("file", nargs="?", default=DEFAULT_FILE, type=pathlib.Path)
    ap.add_argument("--json", action="store_true", help="вывести JSON вместо текста")
    args = ap.parse_args(argv)
    try:
        text = args.file.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        sys.exit(f"не удалось прочитать {args.file}: {e}")
    try:
        s = stats(text, args.file, warn=lambda l: print(f"строка не разобрана: {l}", file=sys.stderr))
    except ValueError as e:
        sys.exit(f"{args.file}: {e}")
    print(json.dumps(s, ensure_ascii=False, indent=2) if args.json else render(s))


if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    main()
