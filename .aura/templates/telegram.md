# Telegram Message Template

This template defines the output format for CineTaste v5 Telegram messages.

## Format

```
📅 {date}

┏━━ СЕГОДНЯ ━━┓

🌟 ОБЯЗАТЕЛЬНО

[① {title}]({url}) — {score}%
[② {title}]({url}) — {score}%
...

👍 РЕКОМЕНДУЮ

[③ {title}]({url}) — {score}%
...

┏━━ 📊 ━━┓
{count} фильмов подходит

📍 {city}
```

## Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `{date}` | Current date | 02.03.2026 |
| `{title}` | Movie title | Человек-бензопила |
| `{url}` | Movie URL | https://kinoteatr.ru/film/... |
| `{score}` | Relevance score | 85 |
| `{count}` | Total movies | 9 |
| `{city}` | City name | Набережные Челны |

## Markdown Support

Telegram supports:
- **Bold**: `**text**`
- *Italic*: `_text_`
- Links: `[text](url)`
- Code: `` `code` ``
- Pre: ` ```code``` `

## Notes

- Keep messages under 4096 characters (Telegram limit)
- Use circled numbers ①②③④⑤⑥⑦⑧⑨⑩ for list items
- Group by recommendation: must_see first, then recommended
