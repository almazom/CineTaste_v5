# Send-Confirmation

**Файл:** `contracts/send-confirmation.schema.json`
**Версия:** 1.0.0
**Производитель:** t2me
**Потребитель:** — (конец пайплайна)

---

## Диаграмма

```
                    send-confirmation
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
     success ✓         message_id          error
        │             (если success)    (если ошибка)
        │
    [true | false]
        │
        └──────► meta
                   │
            ┌──────┼──────┐
            │      │      │
        sent_at ✓ target  char_count


   ┌───────────────────────────────────────────────────┐
   │                                                   │
   │  ✅ УСПЕХ:                                        │
   │  {                                                │
   │    "success": true,                               │
   │    "message_id": 12345,                           │
   │    "meta": {                                      │
   │      "sent_at": "2024-03-15T12:05:00Z",           │
   │      "target": "@username",                       │
   │      "char_count": 1500                           │
   │    }                                              │
   │  }                                                │
   │                                                   │
   ├───────────────────────────────────────────────────┤
   │                                                   │
   │  ❌ ОШИБКА:                                       │
   │  {                                                │
   │    "success": false,                              │
   │    "error": "Network timeout",                    │
   │    "meta": {                                      │
   │      "sent_at": "2024-03-15T12:05:00Z"            │
   │    }                                              │
   │  }                                                │
   │                                                   │
   └───────────────────────────────────────────────────┘
```

---

## Обязательные поля

### Корень
- `success` — успешно ли отправлено (boolean)
- `meta` — метаданные отправки

### Meta
- `sent_at` — время попытки отправки

---

## Условные поля

| Условие | Поле | Описание |
|---------|------|----------|
| `success: true` | `message_id` | ID сообщения в Telegram |
| `success: false` | `error` | Текст ошибки |

---

## Примеры

### Успешная отправка

```json
{
  "success": true,
  "message_id": 12345,
  "meta": {
    "sent_at": "2024-03-15T12:05:00Z",
    "target": "@cinetaste_user",
    "char_count": 1500
  }
}
```

### Ошибка отправки

```json
{
  "success": false,
  "error": "Network timeout after 30s",
  "meta": {
    "sent_at": "2024-03-15T12:05:00Z"
  }
}
```

---

## Аналогия

Это как **квитанция об отправке**:
- `success: true` — письмо доставлено
- `message_id` — номер заказного письма
- `success: false` — письмо вернулось
- `error` — причина возврата
