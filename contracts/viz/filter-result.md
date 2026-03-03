# Filter-Result

**Файл:** `contracts/filter-result.schema.json`
**Версия:** 1.0.0
**Производитель:** ct-filter
**Потребитель:** ct-format

---

## Диаграмма

```
                      filter-result
                            │
           ┌────────────────┴────────────────┐
           │                                 │
     filtered[]                             meta
           │                                 │
      ┌────┴────┐                 ┌──────────┴──────────┐
      │         │                 │                     │
    фильм 1   фильм 2       total_input ✓          thresholds
      │                           matched ✓              │
      │                           filtered_at        ┌──┴──┐
      │                                             │     │
      ├─ movie ✓ ──────────────┐           recommendations[]
      │   ├─ id ✓              │               min_score
      │   ├─ title ✓           │
      │   └─ url ✓             │
      │                        │
      ├─ relevance_score ✓    (0-100)
      ├─ recommendation ✓     [must_see | recommended]
      └─ reasoning            (string)


   ⚠️ ВНИМАНИЕ: Только must_see и recommended проходят!
      maybe и skip отфильтровываются
```

---

## Обязательные поля

### Корень
- `filtered` — массив отфильтрованных фильмов
- `meta` — метаданные фильтрации

### Каждый фильм
- `movie` — данные фильма (id, title, url обязательны)
- `relevance_score` — оценка (0-100)
- `recommendation` — только `must_see` или `recommended`

### Meta
- `total_input` — сколько фильмов пришло на вход
- `matched` — сколько прошло фильтр
- `thresholds` — настройки фильтрации

---

## Логика фильтрации

```
Вход: 100 фильмов
       │
       ├── must_see (score ≥ 85)    ──► ПРОХОДИТ ✓
       ├── recommended (score ≥ 60) ──► ПРОХОДИТ ✓
       ├── maybe (score ≥ 40)       ──► ОТФИЛЬТРОВАН ✗
       └── skip (score < 40)        ──► ОТФИЛЬТРОВАН ✗
       │
Выход: ~15 фильмов (только лучшие)
```

---

## Пример данных

```json
{
  "filtered": [
    {
      "movie": {
        "id": "matrix-1999",
        "title": "Матрица",
        "url": "https://kinoteatr.ru/matrix"
      },
      "relevance_score": 92,
      "recommendation": "must_see",
      "reasoning": "Философская фантастика"
    }
  ],
  "meta": {
    "total_input": 50,
    "matched": 8,
    "thresholds": {
      "recommendations": ["must_see", "recommended"],
      "min_score": 60
    },
    "filtered_at": "2024-03-15T11:30:00Z"
  }
}
```

---

## Аналогия

Это как **сито для золота**:
- Вход: куча песка (все фильмы)
- Выход: только самородки (лучшие фильмы)
- `total_input` → `matched` показывает эффективность
