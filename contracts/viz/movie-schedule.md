# Movie-Schedule

**Файл:** `contracts/movie-schedule.schema.json`
**Версия:** 1.0.0
**Производитель:** ct-schedule
**Потребитель:** ct-analyze

---

## Диаграмма

```
                      movie-schedule
                            │
           ┌────────────────┴────────────────┐
           │                                 │
        movies[]                            meta
           │                                 │
      ┌────┴────┐                   ┌────────┴────────┐
      │         │                   │                 │
   фильм 1   фильм 2             city ✓          fetched_at ✓
      │                         date ✓           scheduled_at ✓
      │                         schedule_source ✓
      │                         city_display
      │                         source_url
      │                         movies_total
      │                         movies_with_showtimes
      │
      ├─ id ✓               (string)
      ├─ title ✓            (string)
      ├─ source ✓           (string)
      ├─ showtimes[] ✓
      │   ├─ time ✓         (HH:MM)
      │   ├─ datetime_iso ✓ (ISO 8601)
      │   ├─ hall           (string)
      │   └─ booking_url    (uri)
      │
      ├─ original_title     (string)
      ├─ director           (string)
      ├─ actors[]           (array of strings)
      ├─ genres[]           (array of strings)
      ├─ year               (integer | null)
      ├─ duration_min       (integer | null)
      ├─ url                (string, uri)
      └─ raw_description    (string)
```

---

## Обязательные поля

### Корень
- `movies` — массив фильмов с расписанием
- `meta` — метаданные обогащения

### Каждый фильм
- `id` — уникальный идентификатор
- `title` — название фильма
- `source` — источник данных
- `showtimes` — массив сеансов (может быть пустым)

### Каждый сеанс
- `time` — локальное время в формате HH:MM
- `datetime_iso` — полная дата/время в ISO 8601

### Meta
- `city` — код города
- `date` — дата расписания (YYYY-MM-DD)
- `fetched_at` — время первичного fetch
- `scheduled_at` — время построения расписания
- `schedule_source` — источник расписания

---

## Аналогия

Это как **афиша + табло сеансов**:
- `movies` — список фильмов
- `showtimes` — конкретные сеансы каждого фильма
- `meta` — когда и откуда расписание собрано
