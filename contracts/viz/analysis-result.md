# Analysis-Result

**Файл:** `contracts/analysis-result.schema.json`
**Версия:** 1.0.0
**Производитель:** ct-cognize
**Потребитель:** ct-filter

---

## Диаграмма

```
                     analysis-result
                           │
          ┌────────────────┴────────────────┐
          │                                 │
     analyzed[]                            meta
          │                                 │
     ┌────┴────┐                  ┌─────────┴─────────┐
     │         │                  │                   │
   анализ 1  анализ 2          analyzer ✓           agent
     │                        analyzed_at ✓    web_search_used
     │                        taste_profile
     │
     ├─ movie ✓ ──────────────────┐
     │   ├─ id ✓                  │
     │   ├─ title ✓               │
     │   ├─ original_title        │
     │   ├─ director              │
     │   ├─ actors[]              │
     │   ├─ genres[]              │
     │   ├─ year                  │
     │   ├─ duration_min          │
     │   ├─ source                │
     │   └─ url                   │
     │                            │
     ├─ relevance_score ✓    (0-100)
     │
     ├─ recommendation ✓     [must_see | recommended | maybe | skip]
     │
     ├─ confidence           (0-1)
     ├─ reasoning            (string)
     ├─ key_matches[]        (array of strings)
     ├─ red_flags[]          (array of strings)
     ├─ rule_score           (0-100, baseline)
     ├─ llm_delta            (bounded correction)
     ├─ review_required      (boolean)
     └─ decision_basis[]     (array of strings)
```

---

## Обязательные поля

### Корень
- `analyzed` — массив проанализированных фильмов
- `meta` — метаданные анализа

### Каждый анализ
- `movie` — исходные данные фильма (id, title обязательны)
- `relevance_score` — оценка соответствия вкусу (0-100)
- `recommendation` — категория рекомендации

### Meta
- `analyzer` — кто анализировал
- `analyzed_at` — когда анализировали
- `quality_policy` — какая rules-first политика применялась
- `review_required_count` — сколько фильмов помечены как спорные

---

## Категории рекомендаций

| Значение | Описание | Score |
|----------|----------|-------|
| `must_see` | Обязательно посмотреть | ≥85 |
| `recommended` | Рекомендуется | ≥60 |
| `maybe` | Может быть | ≥40 |
| `skip` | Пропустить | <40 |

---

## Пример данных

```json
{
  "analyzed": [
    {
      "movie": {
        "id": "matrix-1999",
        "title": "Матрица",
        "director": "Вачовски"
      },
      "relevance_score": 92,
      "confidence": 0.88,
      "recommendation": "must_see",
      "reasoning": "Философская фантастика с глубоким сюжетом",
      "key_matches": ["фантастика", "философия"],
      "red_flags": [],
      "rule_score": 89,
      "llm_delta": 3,
      "review_required": false,
      "decision_basis": ["rule:genre_match", "llm_delta:+3"]
    }
  ],
  "meta": {
    "analyzer": "kimi",
    "analyzed_at": "2024-03-15T11:00:00Z",
    "taste_profile": "v1.2",
    "quality_policy": "rules_first_v1",
    "review_required_count": 0
  }
}
```

---

## Аналогия

Это как **рецензия кинокритика**:
- `relevance_score` — сколько звёзд из 100
- `recommendation` — вердикт: смотреть или нет
- `key_matches` — что понравилось
- `red_flags` — что настораживает
- `rule_score` — детерминированная база до LLM
- `llm_delta` — насколько модель сдвинула базовую оценку
- `review_required` — спорный кейс, который стоит проверить глазами
