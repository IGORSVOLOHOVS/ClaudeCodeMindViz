"""Тесты mmdstats: разбор узлов, фигур, стрелок и подписей; статусы; цепочки (DAG, циклы, длинные); CLI."""
import io
import json
import pathlib
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

import mmdstats

SAMPLE = """# заголовок

```mermaid
flowchart TD
  classDef done fill:#d3f9d8
  Q1["Q: первый вопрос"]:::done
  Q1 --> H1["H: гипотеза раз"]:::rejected
  Q1 --> H2["H: гипотеза два"]:::done
  H2 --> T1["T: проверка"]:::active
  T1 --> A1["A: решение"]
  H2 --> Q2["Q: открытый вопрос"]:::active
  X1(["служебный узел"]):::done
  X1 -.-> Q2
```
"""


def graph(*lines):
    return "flowchart TD\n" + "\n".join("  " + l for l in lines) + "\n"


class ParseTest(unittest.TestCase):
    def test_nodes_and_edges(self):
        nodes, edges = mmdstats.parse(SAMPLE)
        self.assertEqual(set(nodes), {"Q1", "H1", "H2", "T1", "A1", "Q2", "X1"})
        self.assertEqual(len(edges), 6)
        self.assertIn(("X1", "Q2"), edges)

    def test_inline_definition_keeps_label_and_status(self):
        nodes, _ = mmdstats.parse(SAMPLE)
        self.assertEqual(nodes["H1"]["label"], "H: гипотеза раз")
        self.assertEqual(nodes["H1"]["status"], "rejected")
        self.assertEqual(nodes["A1"]["status"], "")
        self.assertEqual(nodes["X1"]["kind"], "-")

    def test_plain_mmd_without_fence(self):
        nodes, edges = mmdstats.parse(graph('A["Q: a"] --> B["H: b"]'))
        self.assertEqual(set(nodes), {"A", "B"})
        self.assertEqual(edges, [("A", "B")])

    def test_edge_labels_all_forms(self):
        nodes, edges = mmdstats.parse(graph('A["Q: a"] -->|"8 тестов OK"| B["H: b"]:::done', 'B -.->|x| C', 'C -- почему --> D', 'D -. пунктир .-> E', 'E == жирно ==> F'))
        self.assertEqual(edges, [("A", "B"), ("B", "C"), ("C", "D"), ("D", "E"), ("E", "F")])
        self.assertEqual(nodes["B"]["status"], "done")

    def test_entity_codes_decoded(self):
        nodes, _ = mmdstats.parse(graph('A["Q: say #quot;hi#quot; #amp; bye"]'))
        self.assertEqual(nodes["A"]["label"], 'Q: say "hi" & bye')

    def test_chains_and_groups(self):
        _, edges = mmdstats.parse(graph("A --> B --> C", "D & E --> F"))
        self.assertEqual(edges, [("A", "B"), ("B", "C"), ("D", "F"), ("E", "F")])

    def test_all_shapes_and_unquoted_labels(self):
        src = graph('A["Q: a"]', 'B("Q: b")', 'C(["Q: c"])', 'D[["Q: d"]]', 'E{{"Q: e"}}', 'F{"Q: f"}',
                    'G(("Q: g"))', 'H>"Q: h"]', 'I[/"Q: i"/]', 'J[Q: без кавычек]', 'K[("Q: k")]')
        nodes, _ = mmdstats.parse(src)
        self.assertEqual(len(nodes), 11)
        self.assertTrue(all(n["kind"] == "Q" for n in nodes.values()), {k: v["label"] for k, v in nodes.items()})
        self.assertEqual(nodes["J"]["label"], "Q: без кавычек")

    def test_arrow_forms(self):
        _, edges = mmdstats.parse(graph("A --- B", "B -.-> C", "C ==> D", "D <--> E", "E --o F", "F ----> G", "G -..-> H"))
        self.assertEqual(len(edges), 7)

    def test_arrow_inside_quotes_is_text(self):
        nodes, edges = mmdstats.parse(graph('A["Q: как парсить --> ?"]:::active --> B["H: a --- b | c"]'))
        self.assertEqual(edges, [("A", "B")])
        self.assertEqual(nodes["A"]["label"], "Q: как парсить --> ?")
        self.assertEqual(nodes["B"]["label"], "H: a --- b | c")

    def test_class_statements(self):
        nodes, _ = mmdstats.parse(graph('Q1["Q: a"]', 'H1["H: b"]', "Q1 --> H1", "class Q1 active", "class H1,Q1 rejected"))
        self.assertEqual(nodes["H1"]["status"], "rejected")
        self.assertEqual(nodes["Q1"]["status"], "rejected")

    def test_skip_needs_word_boundary(self):
        nodes, edges = mmdstats.parse(graph('endpoint["Q: конец?"]:::active', 'styleQ["Q: стиль"]:::active --> graph2["A: граф"]:::done', "A --> endpoint"))
        self.assertEqual(nodes["endpoint"]["label"], "Q: конец?")
        self.assertEqual(nodes["graph2"]["status"], "done")
        self.assertEqual(len(edges), 2)

    def test_unparsed_line_is_reported_and_skipped(self):
        seen = []
        nodes, edges = mmdstats.parse(graph('A["Q: a"] --> B', "это не mermaid ((", "B --> C"), warn=seen.append)
        self.assertEqual(seen, ["это не mermaid (("])
        self.assertEqual(edges, [("A", "B"), ("B", "C")])
        self.assertEqual(set(nodes), {"A", "B", "C"})

    def test_trailing_semicolon_and_crlf(self):
        _, edges = mmdstats.parse("flowchart TD\r\n  A --> B;\r\n  B --> C\r\n")
        self.assertEqual(edges, [("A", "B"), ("B", "C")])


class SourceTest(unittest.TestCase):
    def test_markdown_without_fence_is_rejected(self):
        with self.assertRaises(ValueError):
            mmdstats.parse("# Title\n\nfoo\n\nbar\n", path="README.md")

    def test_non_flowchart_is_rejected(self):
        with self.assertRaises(ValueError):
            mmdstats.parse("```mermaid\nsequenceDiagram\n  A->>B: hi\n```\n")

    def test_unterminated_fence_and_init_directive(self):
        nodes, _ = mmdstats.parse("```mermaid\n%%{init: {}}%%\nflowchart LR\n  A --> B\n")
        self.assertEqual(set(nodes), {"A", "B"})


class StatsTest(unittest.TestCase):
    def test_counts_and_lists(self):
        s = mmdstats.stats(SAMPLE)
        self.assertEqual(s["nodes"], 7)
        self.assertEqual(s["by_kind"]["Q"], {"active": 1, "done": 1, "rejected": 0, "none": 0})
        self.assertEqual(s["by_kind"]["A"]["none"], 1)
        self.assertEqual(s["by_kind"]["-"]["done"], 1)
        self.assertEqual(s["open_questions"], ["Q: открытый вопрос"])
        self.assertEqual(s["rejected"], ["H: гипотеза раз"])

    def test_counts_add_up_in_text_output(self):
        text = mmdstats.render(mmdstats.stats(graph('Q1["Q: a"]:::wip', 'S0["шаг"]', 'Q1 --> S0')))
        self.assertRegex(text, r"вопрос\s+1\s+в работе 0, принято 0, отвергнуто 0, без статуса 1")
        self.assertRegex(text, r"прочие\s+1\s+в работе 0, принято 0, отвергнуто 0, без статуса 1")

    def test_longest_chain_dag(self):
        s = mmdstats.stats(SAMPLE)
        self.assertEqual(s["longest_chain"], ["Q: первый вопрос", "H: гипотеза два", "T: проверка", "A: решение"])

    def test_longest_chain_skips_rejected(self):
        s = mmdstats.stats(graph('Q["Q: q"] --> H["H: bad"]:::rejected --> T["T: t"] --> A["A: a"]', "Q --> B"))
        self.assertEqual(s["longest_chain"], ["Q: q", "B"])

    def test_longest_chain_with_cycle_any_order(self):
        for lines in (("X --> A", "A --> B", "B --> X", "X --> C", "C --> D", "D --> E"),
                      ("A --> B", "B --> X", "X --> A", "X --> C", "C --> D", "D --> E")):
            self.assertEqual(len(mmdstats.stats(graph(*lines))["longest_chain"]), 6, lines)
        self.assertEqual(len(mmdstats.stats(graph("A --> B", "B --> A", "A --> A"))["longest_chain"]), 2)

    def test_long_linear_chain_no_recursion(self):
        s = mmdstats.stats(graph(*[f"S{i} --> S{i + 1}" for i in range(2000)]))
        self.assertEqual(len(s["longest_chain"]), 2001)

    def test_big_cyclic_graph_falls_back(self):
        lines = [f"S{i} --> S{i + 1}" for i in range(400)] + ["S400 --> S0"]
        self.assertEqual(len(mmdstats.stats(graph(*lines))["longest_chain"]), 401)


class CliTest(unittest.TestCase):
    def run_cli(self, argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            try:
                mmdstats.main(argv)
                code = 0
            except SystemExit as e:
                code = e.code
        return code, out.getvalue(), err.getvalue()

    def test_json_output(self):
        with tempfile.TemporaryDirectory() as d:
            p = pathlib.Path(d) / "g.md"
            p.write_text(SAMPLE, encoding="utf-8")
            code, out, _ = self.run_cli([str(p), "--json"])
        data = json.loads(out)
        self.assertEqual(code, 0)
        self.assertEqual(data["nodes"], 7)
        self.assertEqual(data["longest_chain"][-1], "A: решение")

    def test_text_output_mentions_open_question(self):
        with tempfile.TemporaryDirectory() as d:
            p = pathlib.Path(d) / "g.md"
            p.write_text(SAMPLE, encoding="utf-8")
            _, out, _ = self.run_cli([str(p)])
        self.assertIn("Q: открытый вопрос", out)
        self.assertIn("✗ H: гипотеза раз", out)

    def test_missing_and_bad_files(self):
        with tempfile.TemporaryDirectory() as d:
            missing = pathlib.Path(d) / "nope.md"
            code, _, err = self.run_cli([str(missing)])
            self.assertIn("не удалось прочитать", str(code))
            latin = pathlib.Path(d) / "latin.mmd"
            latin.write_bytes("flowchart TD\n  A[\"Q: ошибка\"]\n".encode("cp1251"))
            code, _, _ = self.run_cli([str(latin)])
            self.assertIn("не удалось прочитать", str(code))
            readme = pathlib.Path(d) / "README.md"
            readme.write_text("# hi\n\nfoo\n", encoding="utf-8")
            code, _, _ = self.run_cli([str(readme)])
            self.assertIn("нет блока", str(code))

    def test_real_project_graphs_parse(self):
        root = pathlib.Path(__file__).parent / ".claude" / "decision_graph"
        for p in list(root.glob("*.md")) + list((root / "archive").glob("*.md")):
            with self.subTest(p.name):
                s = mmdstats.stats(p.read_text(encoding="utf-8"), p)
                self.assertGreater(s["nodes"], 0)
                self.assertGreater(len(s["longest_chain"]), 0)


if __name__ == "__main__":
    unittest.main()
