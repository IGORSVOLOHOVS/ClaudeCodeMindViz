#!/usr/bin/env python3
"""mmdstats — статистика по Mermaid-графу решений.

Читает flowchart из .md (первый блок ```mermaid) или .mmd и печатает:
счётчики узлов по типу (Q/H/T/A) и статусу (active/done/rejected),
открытые вопросы, отвергнутые гипотезы и самую длинную цепочку.

Использование:
  python mmdstats.py [файл] [--json]
Файл по умолчанию: .claude/decision_graph/current_task.md
"""
import argparse
import json
import pathlib
import re
import sys

DEFAULT_FILE = pathlib.Path(".claude/decision_graph/current_task.md")
KINDS = {"Q": "вопрос", "H": "гипотеза", "T": "проверка", "A": "решение"}

# Узел: id, затем необязательная фигура с текстом в кавычках, затем необязательный :::статус
NODE_DEF = re.compile(r'^(\w+)\s*(?:[\[({]+"([^"]*)"[\])}]+)?(?::::(\w+))?$')
# Стрелка, за ней необязательная подпись |"текст"|
EDGE_SPLIT = re.compile(r"\s*(?:-->|-\.->|---|==>|-\.-)\s*(?:\|[^|]*\|\s*)?")
SKIP = ("%%", "flowchart", "graph", "classDef", "class ", "style", "linkStyle", "subgraph", "end")
FENCE = re.compile(r"```mermaid[^\n]*\n([\s\S]*?)(?:```|$)")


def mermaid_source(text):
    """Первый блок ```mermaid из Markdown, либо весь текст (для .mmd)."""
    m = FENCE.search(text)
    return m.group(1) if m else text


def parse(text):
    """-> (nodes: {id: {id, label, status, kind}}, edges: [(from, to)])."""
    nodes, edges = {}, []
    for raw in mermaid_source(text).splitlines():
        line = raw.strip()
        if not line or line.startswith(SKIP):
            continue
        ids = []
        for part in EDGE_SPLIT.split(line):
            m = NODE_DEF.match(part.strip())
            if not m:
                ids = []
                break
            nid, label, status = m.groups()
            node = nodes.setdefault(nid, {"id": nid, "label": nid, "status": ""})
            if label is not None:
                node["label"] = label
            if status:
                node["status"] = status
            ids.append(nid)
        edges.extend(zip(ids, ids[1:]))
    for node in nodes.values():
        m = re.match(r"([QHTA]):", node["label"])
        node["kind"] = m.group(1) if m else "-"
    return nodes, edges


def longest_chain(nodes, edges):
    """Самый длинный путь в графе (по числу узлов); циклы не зацикливают."""
    out = {}
    for a, b in edges:
        out.setdefault(a, []).append(b)
    best, memo = [], {}

    def walk(nid, seen):
        if nid in memo:
            return memo[nid]
        path = [nid]
        for nxt in out.get(nid, []):
            if nxt not in seen:
                cand = [nid] + walk(nxt, seen | {nxt})
                if len(cand) > len(path):
                    path = cand
        memo[nid] = path
        return path

    for nid in nodes:
        chain = walk(nid, {nid})
        if len(chain) > len(best):
            best = chain
    return [nodes[n]["label"] for n in best]


def stats(text):
    nodes, edges = parse(text)
    by_kind = {k: {"active": 0, "done": 0, "rejected": 0, "": 0} for k in list(KINDS) + ["-"]}
    for n in nodes.values():
        by_kind[n["kind"]][n["status"] if n["status"] in ("active", "done", "rejected") else ""] += 1
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
    for kind, name in KINDS.items():
        c = s["by_kind"][kind]
        total = sum(c.values())
        if total:
            lines.append(f"{name:9} {total:3}   в работе {c['active']}, принято {c['done']}, отвергнуто {c['rejected']}")
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
    except OSError as e:
        sys.exit(f"не удалось прочитать {args.file}: {e}")
    s = stats(text)
    print(json.dumps(s, ensure_ascii=False, indent=2) if args.json else render(s))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
