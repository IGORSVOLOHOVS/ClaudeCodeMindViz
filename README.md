# claude-code-mind-viz

A console tool that reads a decision graph, kept as a Mermaid flowchart, and prints what stands in it: how many questions, hypotheses, checks and decisions there are in each status, which questions are still open, which hypotheses were rejected, and the longest chain that survived.

The graph is the one a Claude Code session keeps while it works on a long task, in `.claude/decision_graph/current_task.md`. `mmdstats` reads the first `mermaid` block of a Markdown file, or a whole `.mmd` file, line by line. It needs nothing but the Python standard library. It reports in Russian, or as JSON with `--json`.

`.claude/decision_graph/` holds the graph and the action trace from the building of this tool. The tests read them as real input.

## Use

```powershell
.\recipe.ps1 run
.\recipe.ps1 run path\to\graph.md --json
```

`docs/install.md` says what to install and `docs/manual.md` describes the options and the graph format. `.\recipe.ps1 test` runs the tests, mypy and ruff.

## Licence

MIT, see `LICENSE`.

## Lab requirements

This repository complies with [revision 4.0.0](http://127.0.0.1:3000/igors-lab/software-requirements/src/tag/v4.0.0/BEST_REQUIREMENTS.md) of the lab requirements, except R-02 (#8), R-09 (#9), R-37 (#10), R-41 (#11), R-42 (#12).
