# Movie-Batch

**Файл:** `contracts/movie-batch.schema.json`
**Версия:** 1.0.0
**Производитель:** ct-fetch
**Потребитель:** ct-schedule

---

## Диаграмма

```
                        movie-batch
                             │
             ┌───────────────┴───────────────┐
             │                               │
         movies[]                          meta
             │                               │
        ┌────┴────┐                   ┌──────┴──────┐
        │         │                   │             │
      фильм 1   фильм 2            city ✓       fetched_at ✓
        │                            │
        │                            date ✓
        │                            city_display
        │                            source_url
        │
        ├─ id ✓              (string)
        ├─ title ✓           (string)
        ├─ source ✓          (string)
        │
        ├─ original_title    (string)
        ├─ director          (string)
        ├─ actors[]          (array of strings)
        ├─ genres[]          (array of strings)
        ├─ year              (integer | null)
        ├─ duration_min      (integer | null)
        ├─ url               (string, uri)
        └─ raw_description   (string)
```

---

## Обязательные поля

### Корень
- `movies` — массив фильмов
- `meta` — метаданные запроса

### Каждый фильм
- `id` — уникальный идентификатор
- `title` — название на русском
- `source` — источник (например, "kinoteatr.ru")

### Meta
- `city` — код города
- `date` — дата запроса (YYYY-MM-DD)
- `fetched_at` — время запроса (ISO 8601)

---

## Пример данных

```json
{
  "movies": [
    {
      "id": "matrix-1999",
      "title": "Матрица",
      "director": "Вачовски",
      "genres": ["фантастика", "боевик"],
      "year": 1999,
      "source": "kinoteatr.ru",
      "url": "https://..."
    }
  ],
  "meta": {
    "city": "msk",
    "date": "2024-03-15",
    "fetched_at": "2024-03-15T10:30:00Z"
  }
}
```

---

## Аналогия

Это как **корзина с фильмами** из кинотеатра:
- `movies` — сами фильмы
- `meta` — штамп: где, когда, кем собрано
