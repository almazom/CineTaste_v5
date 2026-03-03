# Contract Visualizations

ASCII-диаграммы для всех контрактов проекта CineTaste.

## Файлы

| Файл | Контракт | Описание |
|------|----------|----------|
| [movie-batch.md](./movie-batch.md) | `movie-batch.schema.json` | Сырые фильмы из кинотеатра |
| [movie-schedule.md](./movie-schedule.md) | `movie-schedule.schema.json` | Фильмы с расписанием сеансов |
| [analysis-result.md](./analysis-result.md) | `analysis-result.schema.json` | Фильмы с оценкой вкуса |
| [filter-result.md](./filter-result.md) | `filter-result.schema.json` | Отфильтрованные лучшие фильмы |
| [message-text.md](./message-text.md) | `message-text.schema.json` | Telegram сообщение |
| [send-confirmation.md](./send-confirmation.md) | `send-confirmation.schema.json` | Статус доставки |

## Поток данных

```
ct-fetch --> ct-schedule --> ct-analyze --> ct-filter --> ct-format --> t2me
    |             |             |             |             |          |
    v             v             v             v             v          v
movie-batch  movie-schedule  analysis    filter-result  message-text  send-confirm
```

## Как читать диаграммы

```
✓  — обязательное поле
[] — массив
{} — объект
```
