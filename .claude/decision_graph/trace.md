# Трасса действий

_Пишет хук action_trace.sh — не редактировать вручную._

Цвета: жёлтый шестиугольник — поставлен вопрос, зелёный — принято решение, красный — отвергнуто или ошибка; серые — шаги агентов, синие — сами агенты. На стрелках — результат предыдущего шага.

```mermaid
flowchart TD
  classDef agentHead fill:#e7f5ff,stroke:#1c7ed6,stroke-width:2px,color:#212529
  classDef agentStep fill:#f1f3f5,stroke:#868e96,color:#212529
  classDef failed fill:#ffe3e3,stroke:#c92a2a,stroke-width:2px,color:#212529
  classDef decision fill:#fff3bf,stroke:#f08c00,stroke-width:2px,color:#212529
  classDef decisionDone fill:#d3f9d8,stroke:#2f9e44,stroke-width:2px,color:#212529
  classDef decisionRejected fill:#ffe3e3,stroke:#c92a2a,stroke-dasharray:4 3,color:#212529
  S0["Архив прошлого графа"]
  S1{{"Q: язык и зависимости"}}:::decision
  S0 --> S1
  S2{{"Q: как разбирать Mermaid ✓"}}:::decision
  S1 --> S2
  S3{{"Q: откуда брать путь… ✓"}}:::decision
  S2 --> S3
  S4["Записал mmdstats.py"]
  S3 --> S4
  S5["Записал test_mmdstats.py"]
  S4 --> S5
  S6["Правил mmdstats.py"]
  S5 --> S6
  S7["Тесты и прогон mmdstats"]
  S6 --> S7
  S8{{"T: unittest на образце… ✓"}}:::decision
  S7 --> S8
  S9{{"Q: формат вывода ✓"}}:::decision
  S8 --> S9
  S10["Workflow: verify-mmdstats"]
  S9 --> S10
  A_a4a4bab162af8a2bf(["Агент workflow-subagent · a4a4bab"]):::agentHead
  S10 -.-> A_a4a4bab162af8a2bf
  S11["Читал mmdstats.py"]:::agentStep
  A_a4a4bab162af8a2bf --> S11
  S12["Читал test_mmdstats.py"]:::agentStep
  S11 --> S12
  A_a1dec565426bf74bc(["Агент workflow-subagent · a1dec56"]):::agentHead
  S10 -.-> A_a1dec565426bf74bc
  S13["Читал test_mmdstats.py"]:::agentStep
  A_a1dec565426bf74bc --> S13
  S14["Читал mmdstats.py"]:::agentStep
  S13 --> S14
  S15["Читал current_task.md"]:::agentStep
  S12 --> S15
  S16["Читал current_task.md"]:::agentStep
  S14 --> S16
  S17["Читал 2026-09-23-setup-current_task.md"]:::agentStep
  S15 --> S17
  S18["Читал 2026-09-23-setup-current_task.md"]:::agentStep
  S16 --> S18
  S19["Читал 2026-09-23-setup-trace.md"]:::agentStep
  S17 --> S19
  S20["Читал 2026-09-23-setup-trace.md"]:::agentStep
  S18 --> S20
  S21["Запуск существующих тестов"]:::agentStep
  S20 --> S21
  S22["Прогон на реальных файлах"]:::agentStep
  S21 --> S22
  S23["JSON трассы и подсчёт"]:::agentStep
  S22 --> S23
  S24["JSON текущей задачи"]:::agentStep
  S23 --> S24
  S25["Снимок трассы демо"]
  S10 --> S25
  S26["Читал shot_demo.png"]
  S25 --> S26
  S27{{"Граф решений обновлён"}}:::decision
  S26 --> S27
  S28["Отчёт агентов проверки"]
  S27 --> S28
  S29["Запуск юнит-тестов"]:::agentStep
  S19 --> S29
  S30["Прогон на current_task.md"]:::agentStep
  S29 --> S30
  S31["Прогон на архивном графе"]:::agentStep
  S30 --> S31
  S32["Прогон на трассе"]:::agentStep
  S31 --> S32
  S33["Записал probe.py"]:::agentStep
  S24 --> S33
  S34["Записал probe_chain.py"]:::agentStep
  S33 --> S34
  S35["Дамп рёбер current_task.md"]:::agentStep
  S32 --> S35
  S36["Записал probe_render.py"]:::agentStep
  S34 --> S36
  S37["Проверка валидности JSON"]:::agentStep
  S35 --> S37
  S38["Проверка фигур и стрелок"]:::agentStep
  S36 --> S38
  S39["Проверка длинной цепочки"]:::agentStep
  S38 --> S39
  S40["Проверка вывода render"]:::agentStep
  S39 --> S40
  S41["Проверка ошибок и путей"]:::agentStep
  S40 --> S41
  S42["Записал driver.py"]:::agentStep
  S37 --> S42
  S43["Читал current_task.md"]:::agentStep
  S42 --> S43
  S44["Прогон краевых случаев"]:::agentStep
  S43 --> S44
  S45["✗ Кодировка stderr в PowerShell"]:::failed
  S41 --> S45
  S46["Частичный разбор строки"]:::agentStep
  S45 --> S46
  S47["Форма tool_response в payload"]
  S28 --> S47
  S48["Правил CLAUDE.md"]
  S47 --> S48
  S49{{"Q: язык и зависимости"}}:::decision
  S48 --> S49
  S50["Правил mmdstats.py"]
  S49 --> S50
  S51["Правил test_mmdstats.py"]
  S50 --> S51
  S52["Правил graph_viewer.py"]
  S51 --> S52
  S53["Инструмент: select:mcp__claude_ai_Mermaid…"]:::agentStep
  S44 --> S53
  S54["Порог рекурсии и время"]:::agentStep
  S53 --> S54
  S55["Кодировка stderr при перенаправлении"]:::agentStep
  S54 --> S55
  S56["Mermaid Chart: validate and… ×7"]:::agentStep
  S55 --> S56
  S57["Проверка валидности end_ids"]:::agentStep
  S56 --> S57
  S58["Вернул результат"]:::agentStep
  S46 --> S58
  S59["Записал action_trace.sh"]
  S52 --> S59
  S60["Mermaid Chart: validate and…"]
  S59 --> S60
  S61["Тесты парсера со стрелками"]
  S60 --> S61
  S62["Результат валидации графа"]
  S61 --> S62
  S63["Тест стрелок и цветов"]
  S62 --> S63
  S64["Легенда в живой трассе"]
  S63 --> S64
  S65["Отчёт агентов проверки"]
  S64 --> S65
  S66["Вернул результат"]:::agentStep
  S57 --> S66
  S67["Правил action_trace.sh"]
  S65	Отчёт агентов проверки	1		 verify:edge-cases calls: 25 running --> S67
  S68["Правил action_trace.sh"]
  S67	Правил action_trace.sh	1		правка внесена --> S68
  S69["Правил action_trace.sh"]
  S68	Правил action_trace.sh	1		правка внесена --> S69
  S70["Правил action_trace.sh"]
  S69	Правил action_trace.sh	1		правка внесена --> S70
  S71{{"Q: что чинить из…"}}:::decision
  S70 -->|"правка внесена"| S71
  S72["Записал mmdstats.py"]
  S71 -->|"правка внесена"| S72
  S73["Записал test_mmdstats.py"]
  S72 -->|"файл обновлён"| S73
  S74["Читал task_labels.png"]
  S73 -->|"файл обновлён"| S74
  S75["Правил mmdstats.py ×3"]
  S74 --> S75
  S76["Правил test_mmdstats.py"]
  S75 -->|"правка внесена"| S76
  S77["Тесты новой версии mmdstats"]
  S76 -->|"правка внесена"| S77
  S78["Формат состояния трассы"]
  S77 -->|"10. A: mmdstats.py +…"| S78
  S79["Повтор теста стрелок хука"]
  S78 -->|"main: S77Тесты новой версии…"| S79
  S80["Правил mmdstats.py ×2"]
  S79 -->|"--- state main: S10Список…"| S80
  S81["Правил test_mmdstats.py"]
  S80 -->|"правка внесена"| S81
  S82["Записал .gitignore"]
  S81 -->|"правка внесена"| S82
```
