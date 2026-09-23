# Трасса действий

_Пишет хук action_trace.sh — не редактировать вручную._

```mermaid
flowchart TD
  classDef agentHead fill:#e7f5ff,stroke:#1c7ed6,stroke-width:2px,color:#212529
  classDef agentStep fill:#f1f3f5,stroke:#868e96,color:#212529
  classDef failed fill:#ffe3e3,stroke:#c92a2a,stroke-width:2px,color:#212529
  classDef decision fill:#fff3bf,stroke:#f08c00,stroke-width:2px,color:#212529
  S0["Тест: лимит 4 слова,…"]
  S1["Сброс живой трассы"]
  S0 --> S1
  S2["Регрессия скрипта трассировки"]
  S1 --> S2
  S3{{"Q: трасса линейна, дубли,… +2"}}:::decision
  S2 --> S3
  S4["Правил action_trace.sh"]
  S3 --> S4
  S5["Рендер живой трассы"]
  S4 --> S5
  S6["Проверка длины узлов-решений"]
  S5 --> S6
  S7["Читал shot_words.png"]
  S6 --> S7
  S8{{"A: лимит… → done"}}:::decision
  S7 --> S8
  S9["Правил action_trace.sh"]
  S8 --> S9
  S10["Проверка значков статуса"]
  S9 --> S10
  S11["Вопрос пользователю"]
  S10 --> S11
```
