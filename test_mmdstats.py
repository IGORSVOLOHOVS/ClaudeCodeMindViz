"""Тесты mmdstats: разбор узлов и рёбер, статусы, блок в Markdown, длинная цепочка, JSON."""
import io
import json
import pathlib
import tempfile
import unittest
from contextlib import redirect_stdout

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

    def test_edge_labels_are_skipped(self):
        nodes, edges = mmdstats.parse('flowchart TD\n  A["Q: a"] -->|"8 тестов OK"| B["H: b"]:::done\n  B -.->|x| C\n')
        self.assertEqual(edges, [("A", "B"), ("B", "C")])
        self.assertEqual(nodes["B"]["status"], "done")

    def test_plain_mmd_without_fence(self):
        nodes, edges = mmdstats.parse('flowchart TD\n  A["Q: a"] --> B["H: b"]\n')
        self.assertEqual(set(nodes), {"A", "B"})
        self.assertEqual(edges, [("A", "B")])


class StatsTest(unittest.TestCase):
    def test_counts_and_lists(self):
        s = mmdstats.stats(SAMPLE)
        self.assertEqual(s["nodes"], 7)
        self.assertEqual(s["by_kind"]["Q"], {"active": 1, "done": 1, "rejected": 0, "": 0})
        self.assertEqual(s["open_questions"], ["Q: открытый вопрос"])
        self.assertEqual(s["rejected"], ["H: гипотеза раз"])

    def test_longest_chain(self):
        s = mmdstats.stats(SAMPLE)
        self.assertEqual(s["longest_chain"], ["Q: первый вопрос", "H: гипотеза два", "T: проверка", "A: решение"])

    def test_cycle_does_not_hang(self):
        s = mmdstats.stats('flowchart TD\n  A --> B\n  B --> A\n')
        self.assertEqual(len(s["longest_chain"]), 2)


class CliTest(unittest.TestCase):
    def test_json_output(self):
        with tempfile.TemporaryDirectory() as d:
            p = pathlib.Path(d) / "g.md"
            p.write_text(SAMPLE, encoding="utf-8")
            buf = io.StringIO()
            with redirect_stdout(buf):
                mmdstats.main([str(p), "--json"])
            data = json.loads(buf.getvalue())
            self.assertEqual(data["nodes"], 7)
            self.assertIn("longest_chain", data)

    def test_text_output_mentions_open_question(self):
        buf = io.StringIO()
        with tempfile.TemporaryDirectory() as d:
            p = pathlib.Path(d) / "g.md"
            p.write_text(SAMPLE, encoding="utf-8")
            with redirect_stdout(buf):
                mmdstats.main([str(p)])
        self.assertIn("Q: открытый вопрос", buf.getvalue())
        self.assertIn("✗ H: гипотеза раз", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
