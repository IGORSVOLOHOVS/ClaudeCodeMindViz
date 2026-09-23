# Задача: утилита mmdstats — статистика по графу решений

Цель: CLI, который читает граф из `current_task.md` и печатает открытые вопросы,
отвергнутые гипотезы, счётчики по типам/статусам и самую длинную цепочку.

Цвета: жёлтый — в работе, зелёный — принято, красный пунктир — отвергнуто. На стрелках — данные, которые перешли дальше.

```mermaid
flowchart TD
  classDef active fill:#fff3bf,stroke:#f08c00,stroke-width:2px,color:#212529
  classDef done fill:#d3f9d8,stroke:#2f9e44,color:#212529
  classDef rejected fill:#ffe3e3,stroke:#c92a2a,stroke-dasharray:4 3,color:#212529

  Q1["Q: язык и зависимости"]:::done
  Q1 -->|"есть Python 3.13, jq нет"| H1["H: Python, только stdlib — как просмотрщик"]:::done
  Q1 -->|"нужны Node + npm i mermaid"| H2["H: Node + парсер mermaid"]:::rejected
  H1 -->|"вход: current_task.md, 13 узлов, 12 рёбер"| Q2["Q: как разбирать Mermaid"]:::done
  Q2 -->|"строка вида Q1[«Q: …»]:::done"| H3["H: regex по строкам: узлы, рёбра, :::статус"]:::done
  Q2 -->|"грамматика flowchart — сотни правил"| H4["H: полная грамматика flowchart"]:::rejected
  H1 -->|"читают и человек, и скрипт"| Q3["Q: формат вывода"]:::done
  Q3 -->|"скрипту нечего парсить"| H5["H: только текст"]:::rejected
  Q3 -->|"--json → nodes: 13, edges: 12"| H6["H: текст + флаг --json"]:::done
  H1 -->|"запуск из папки проекта"| Q4["Q: откуда брать путь к файлу"]:::done
  Q4 -->|"python mmdstats.py [файл] [--json]"| A1["A: аргумент CLI, по умолчанию .claude/decision_graph/current_task.md"]:::done
  H3 -->|"образец: 7 узлов, 6 рёбер, 3 статуса"| T1["T: unittest на образце графа — 8 тестов"]:::done
  T1 -->|"Ran 8 tests in 0.008s: OK"| T2["T: прогон на реальном current_task.md"]:::done
  T2 -->|"открытый вопрос: Q3 формат вывода"| T3["T: агенты: краевые случаи парсера + код-ревью"]:::active
  T3 -->|"отчёт: findings + verified_ok"| A2["A: mmdstats.py + test_mmdstats.py"]:::active
```
