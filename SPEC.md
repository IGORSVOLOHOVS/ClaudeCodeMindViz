# SPEC — claude-code-mind-viz (`mmdstats`)

Software requirements specification reverse-engineered from the code at commit `eb73f59` (2026-11-08). Documentation hub: [`docs/README.md`](docs/README.md).

## 1. Purpose and scope

`mmdstats` reads a decision graph kept as a Mermaid flowchart and prints statistics about it (`README.md`, `src/mmdstats.py:1-18`).

In scope:
- extracting a flowchart from a Markdown file or a `.mmd` file;
- line-by-line parsing of nodes, edges, labels and status classes;
- counts by node kind and status, open questions, rejected nodes, longest non-rejected chain;
- a Russian text report and a JSON output;
- the CLI `python src/mmdstats.py [file] [--json]`.

Out of scope (absent from the code):
- drawing or rendering the graph;
- writing or editing graph files;
- Mermaid diagram types other than `flowchart`/`graph`;
- the trace hook that once wrote `.claude/decision_graph/trace.md` (its script is not in the repository, `docs/manual.md`).

## 2. Context

- Actors: a person or a Claude Code session running the CLI in a repository that keeps `.claude/decision_graph/current_task.md` (`CLAUDE.md`, "The decision graph"). No other users are named.
- External systems: none. The tool uses only the Python standard library (`pyproject.toml`: `dependencies = []`) and the local file system.
- Runtime: CPython `>=3.13,<3.14` (`pyproject.toml`); started directly, via `recipe.ps1 run` (`uv run --frozen python src/mmdstats.py`, `recipe.ps1:61`), or as `python -m mmdstats` from a built wheel (`docs/install.md`).

## 3. Functional requirements

### 3.1 Input extraction

- **FR-1.** The system shall take the content of the first ```` ```mermaid ```` fenced block when the text contains one, also when the block is not closed. Source: `src/mmdstats.py:33`, `55-57`. Verification: `SourceTest.test_unterminated_fence_and_init_directive`.
- **FR-2.** The system shall reject a file whose name ends in `.md` and has no `mermaid` block, with the message `нет блока ```mermaid`. Source: `src/mmdstats.py:58-59`. Verification: `SourceTest.test_markdown_without_fence_is_rejected`, `CliTest.test_missing_and_bad_files`.
- **FR-3.** The system shall use the whole text of a file not ending in `.md` when it has no `mermaid` block. Source: `src/mmdstats.py:60-61`. Verification: `ParseTest.test_plain_mmd_without_fence`.
- **FR-4.** The system shall reject the source when its first non-empty line that is not a `%%` comment does not start with the word `flowchart` or `graph`. Source: `src/mmdstats.py:62-64`. Verification: `SourceTest.test_non_flowchart_is_rejected`.

### 3.2 Parsing

- **FR-5.** The system shall skip empty lines and lines starting with the words `%%`, `flowchart`, `graph`, `classDef`, `style`, `linkStyle`, `subgraph`, `end`, `direction`, `click`, `accTitle`, `accDescr` (the keywords, though not `%%`, matched on a word boundary). Source: `src/mmdstats.py:35-37`, `96`. Verification: `ParseTest.test_skip_needs_word_boundary`.
- **FR-6.** The system shall strip a trailing `;` and surrounding whitespace (including `\r`) from each line. Source: `src/mmdstats.py:95`. Verification: `ParseTest.test_trailing_semicolon_and_crlf`.
- **FR-7.** The system shall set the status of every node listed in a `class A,B status` statement, creating nodes that do not exist yet. Source: `src/mmdstats.py:38`, `98-102`. Verification: `ParseTest.test_class_statements`.
- **FR-8.** The system shall recognise a node as `id`, an optional shape in any of Mermaid's brackets with a quoted or unquoted label, and an optional `:::status` suffix. Source: `src/mmdstats.py:40`. Verification: `ParseTest.test_all_shapes_and_unquoted_labels`, `ParseTest.test_inline_definition_keeps_label_and_status`.
- **FR-9.** The system shall treat text inside double quotes as label text, so that arrows or `&` inside quotes do not split the line. Source: `src/mmdstats.py:41-42`, `74-75`, `82`. Verification: `ParseTest.test_arrow_inside_quotes_is_text`.
- **FR-10.** The system shall remove edge labels in the forms `|text|`, `-- text -->`, `== text ==>` and `-. text .->`. Source: `src/mmdstats.py:44-49`, `76-77`. Verification: `ParseTest.test_edge_labels_all_forms`.
- **FR-11.** The system shall split a line on the arrows `-->`, `<-->`, `---`, `-.->`, `-.-`, `==>`, `===`, `--o`, `--x` and `~~~`, and add an edge from every node of one segment to every node of the next, with `&` separating nodes inside a segment. Source: `src/mmdstats.py:50`, `79-88`, `108-120`. Verification: `ParseTest.test_arrow_forms`, `ParseTest.test_chains_and_groups`.
- **FR-12.** The system shall decode Mermaid entity codes `#name;` and HTML entities in labels. Source: `src/mmdstats.py:115`. Verification: `ParseTest.test_entity_codes_decoded`.
- **FR-13.** The system shall use the node id as its label until a shape with a label is seen, and keep the last label and the last status given for a node. Source: `src/mmdstats.py:68-69`, `113-117`. Verification: `ParseTest.test_inline_definition_keeps_label_and_status`.
- **FR-14.** The system shall pass every line it cannot parse to a warning callback and continue with the next line; the CLI prints it to stderr as `строка не разобрана: <line>`. Source: `src/mmdstats.py:103-107`, `228`. Verification: `ParseTest.test_unparsed_line_is_reported_and_skipped`.
- **FR-15.** The system shall assign a node the kind `Q`, `H`, `T` or `A` when its label starts with that letter followed by `:`, and kind `-` otherwise. Source: `src/mmdstats.py:121-123`. Verification: `StatsTest.test_counts_and_lists`.

### 3.3 Statistics

- **FR-16.** The system shall count nodes and parsed edges. Source: `src/mmdstats.py:191-192`. Verification: `ParseTest.test_nodes_and_edges`, `CliTest.test_json_output`.
- **FR-17.** The system shall count, for each kind `Q`, `H`, `T`, `A`, `-`, the nodes with status `active`, `done`, `rejected`, and with any other or no status as `none`. Source: `src/mmdstats.py:187-189`. Verification: `StatsTest.test_counts_and_lists`, `StatsTest.test_counts_add_up_in_text_output`.
- **FR-18.** The system shall list as open questions the labels of `Q` nodes with status `active`. Source: `src/mmdstats.py:194`. Verification: `StatsTest.test_counts_and_lists`.
- **FR-19.** The system shall list the labels of all nodes with status `rejected`, of any kind. Source: `src/mmdstats.py:195`. Verification: `StatsTest.test_counts_and_lists`.

### 3.4 Longest chain

- **FR-20.** The system shall return the labels of the longest path, counted in nodes, through nodes whose status is not `rejected`, ignoring self-loops and duplicate edges. Source: `src/mmdstats.py:127-138`, `164`. Verification: `StatsTest.test_longest_chain_dag`, `StatsTest.test_longest_chain_skips_rejected`.
- **FR-21.** For an acyclic graph the system shall compute the chain iteratively over a topological order, without recursion. Source: `src/mmdstats.py:144-154`, `167-182`. Verification: `StatsTest.test_long_linear_chain_no_recursion` (2001 nodes).
- **FR-22.** For a cyclic graph of at most 300 non-rejected nodes the system shall find the longest simple path by enumeration. Source: `src/mmdstats.py:31`, `155-163`. Verification: `StatsTest.test_longest_chain_with_cycle_any_order`.
- **FR-23.** For a cyclic graph of more than 300 non-rejected nodes the system shall drop edges that point back in declaration order and then compute the chain over a topological order. Source: `src/mmdstats.py:140-143`. Verification: `StatsTest.test_big_cyclic_graph_falls_back`.

### 3.5 Output and CLI

- **FR-24.** The system shall accept one optional positional file argument, defaulting to `.claude/decision_graph/current_task.md`, and a `--json` flag. Source: `src/mmdstats.py:28`, `218-222`. Verification: `CliTest.test_json_output`.
- **FR-25.** Without `--json` the system shall print a Russian report: node and edge counts, one line per kind that has nodes, open questions (or `— нет`), rejected nodes (or `— ничего`), and the numbered longest chain. Source: `src/mmdstats.py:200-215`. Verification: `CliTest.test_text_output_mentions_open_question`, `StatsTest.test_counts_add_up_in_text_output`.
- **FR-26.** With `--json` the system shall print the statistics as indented JSON with non-ASCII characters unescaped. Source: `src/mmdstats.py:231`. Verification: `CliTest.test_json_output`.
- **FR-27.** The system shall exit with status 1 and a message naming the file when the file cannot be read or is not valid UTF-8, or when FR-2 or FR-4 rejects it. Source: `src/mmdstats.py:223-230`. Verification: `CliTest.test_missing_and_bad_files` (exit code 1 itself is not asserted; the test checks the message).
- **FR-28.** When run as a script or module, the system shall reconfigure stdout and stderr to UTF-8. Source: `src/mmdstats.py:234-238`. Verification: no test.
- **FR-29.** The system shall parse the graphs in this repository's `.claude/decision_graph/` and `archive/` with at least one node and a non-empty chain each. Source: `.claude/decision_graph/`. Verification: `CliTest.test_real_project_graphs_parse`.

### 3.6 Repository standard

- **FR-30.** The repository shall follow the lab repository standard (repo-quality-template), revision 4.0.0 of the lab requirements, with the exceptions R-02, R-09, R-37, R-41, R-42 listed in `README.md`. Source: `README.md`, `recipe.ps1`. Verification: the template's own checks (`.gitea/workflows/`).

### 3.7 Declared but not implemented

Nothing found: `README.md`, `docs/manual.md` and `docs/install.md` describe only behaviour present in `src/mmdstats.py`, and the source contains no TODO markers.

## 4. Interfaces

### 4.1 CLI

| Item | Value | Source |
| --- | --- | --- |
| invocation | `python src/mmdstats.py [file] [--json]`, `.\recipe.ps1 run [file] [--json]`, `python -m mmdstats` (installed wheel) | `src/mmdstats.py:8-9`, `recipe.ps1:61`, `docs/install.md` |
| `file` | path; default `.claude/decision_graph/current_task.md` | `src/mmdstats.py:220` |
| `--json` | JSON instead of text | `src/mmdstats.py:221` |
| stdout | report or JSON | `src/mmdstats.py:231` |
| stderr | `строка не разобрана: <line>` for each unparsed line | `src/mmdstats.py:228` |
| exit 0 | success, also when lines were skipped | `src/mmdstats.py:218-231` |
| exit 1 | `не удалось прочитать <file>: <error>` or `<file>: <reason>` | `src/mmdstats.py:226`, `230` |

### 4.2 Python API

| Function | Returns | Source |
| --- | --- | --- |
| `mermaid_source(text, path="")` | flowchart source; raises `ValueError` | `src/mmdstats.py:53` |
| `parse(text, path="", warn=None)` | `(nodes, edges)` | `src/mmdstats.py:91` |
| `longest_chain(nodes, edges)` | list of labels | `src/mmdstats.py:127` |
| `stats(text, path="", warn=None)` | statistics dict (section 5) | `src/mmdstats.py:185` |
| `render(stats)` | report text | `src/mmdstats.py:200` |
| `main(argv=None)` | CLI entry | `src/mmdstats.py:218` |

### 4.3 Input format

A Mermaid flowchart; node kind from the label prefix `Q:`/`H:`/`T:`/`A:`, status from the class `active`/`done`/`rejected` (`docs/manual.md`, "The graph format"; `CLAUDE.md`, "The decision graph").

## 5. Data

- Node: `{id, label, status, kind}`; `status` is `""` when none was given; `kind` is `Q`, `H`, `T`, `A` or `-` (`src/mmdstats.py:68-69`, `121-123`).
- Edge: tuple `(from_id, to_id)` (`src/mmdstats.py:119`).
- Statistics / JSON output (`src/mmdstats.py:190-197`):

| Key | Type |
| --- | --- |
| `nodes` | int |
| `edges` | int |
| `by_kind` | object `Q`/`H`/`T`/`A`/`-` → `{active, done, rejected, none}` ints |
| `open_questions` | list of labels |
| `rejected` | list of labels |
| `longest_chain` | list of labels, in path order |

- Storage: none. The tool only reads the input file as UTF-8 (`src/mmdstats.py:224`).

## 6. Non-functional requirements

- **NFR-1.** No runtime dependencies beyond the Python standard library. Source: `pyproject.toml` (`dependencies = []`), imports at `src/mmdstats.py:20-26`.
- **NFR-2.** Python `>=3.13,<3.14`; ruff and mypy target 3.13. Source: `pyproject.toml`.
- **NFR-3.** The longest-chain computation for acyclic graphs is iterative and handles a 2001-node chain. Source: `src/mmdstats.py:130-131`; `test_mmdstats.py`, `test_long_linear_chain_no_recursion`.
- **NFR-4.** Line coverage of `src` by the test suite is at least 97 %. Source: `pyproject.toml` (`--cov-fail-under=97`).
- **NFR-5.** The repository passes `ruff check .` (rules `E4`, `E7`, `E9`, `F`, `I`, line length 120) and `ruff format .` (excluding `.claude/**`, `tests/manual/serve.py`, `tools/wiki.py`); `mypy` passes on `src` and `tools`. Source: `pyproject.toml`, `recipe.ps1:101-107`.
- **NFR-6.** Report and error messages are in Russian; output is written as UTF-8. Source: `src/mmdstats.py:200-215`, `226-238`.

## 7. Constraints and dependencies

| Item | Version | Source |
| --- | --- | --- |
| Python | `>=3.13,<3.14` | `pyproject.toml` |
| setuptools (build backend) | 80.9.0 | `pyproject.toml` |
| ruff | 0.16.1 (also `required-version`) | `pyproject.toml`, `uv.lock` |
| mypy | 2.3.0 | `pyproject.toml` |
| pytest | 8.4.2 | `pyproject.toml` |
| pytest-cov | 5.0.0 | `pyproject.toml` |
| coverage | 7.15.2 | `pyproject.toml` |
| uv | not pinned in the repository | `docs/install.md` |

The module is packaged as a single `py-module` from `src/`, with no console script; uv does not install the project (`package = false`) (`pyproject.toml`). Licence MIT (`LICENSE`, `pyproject.toml`).

## 8. Acceptance

1. `uv sync --frozen` (`docs/install.md`), then `.\recipe.ps1 test` exits 0: version match, pytest with coverage ≥ 97 %, mypy, ruff check, ruff format leaves no diff (`recipe.ps1:82-109`).
2. Without uv: `PYTHONPATH=src python -m unittest test_mmdstats` from the repository root passes all 27 tests (checked 2026-11-19 with Python 3.13.3: OK).
3. `.\recipe.ps1 run` on the repository's own `current_task.md` prints a report and exits 0; `.\recipe.ps1 run <file> --json` prints JSON with the keys of section 5.
4. A Markdown file without a `mermaid` block, a non-flowchart diagram and a missing file each end with exit code 1 and a message (FR-27).

## 9. Open questions

- Who besides the repository owner is expected to use the tool, and in which repositories, is not stated.
- No target sizes or time limits are stated. Enumeration of simple paths for cyclic graphs up to 300 nodes (FR-22) has no measured bound; whether that is acceptable is not documented.
- Whether `class` statements and repeated `:::status` suffixes should accumulate classes as Mermaid does, instead of keeping the last one (FR-7, FR-13), is not decided in the repository. Partly answered: `CLAUDE.md` ("The decision graph") forbids a second `X:::done` line because classes add up, so graphs written to its rules do not hit the difference.
- Whether a node with an unknown class (e.g. `:::todo`) should be reported separately rather than as "no status" (FR-17) is not stated.
- The content and status of the exceptions R-37, R-41, R-42 (issues #10–#12) cannot be read from the repository; the requirements document is linked only on a local server (`README.md`).
- The scratch clone of repo-quality-template available for comparison has no `recipe.ps1` or `.gitea/`, so the exact template revision this repository's tooling came from could not be diffed.
