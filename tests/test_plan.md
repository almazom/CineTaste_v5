# Test Plan: CineTaste v5

**Phase:** 7.5 — Universal Integration Testing  
**Created:** 2026-03-10  
**Author:** Prometheus-Vassa Plamenny (Fire-Testing Architect)

---

## Тип проекта

**CLI Pipeline Tool** с интеграцией Telegram Bot

| Характеристика | Значение |
|----------------|----------|
| **Тип** | CLI pipeline orchestration |
| **Entry Point** | `./run` script |
| **Tech Stack** | Python + Bash |
| **Test Framework** | pytest + pytest-bdd (Gherkin) |
| **External Integration** | kinoteatr.ru (source), Telegram Bot API |

---

## Entry Points

### 1. Pipeline Entry Point
- **Команда:** `./run`
- **Что делает:** Запускает полный pipeline из 6 этапов
- **Слои:** CLI args → Bash orchestrator → Tool chain → Telegram

### 2. Pipeline с опциями
- **Команда:** `./run --dry-run`
- **Что делает:** Полный pipeline без живой отправки в Telegram
- **Слои:** CLI → Orchestrator → Tools → t2me (dry-run mode)

### 3. Replay из кэша
- **Команда:** `./run --input <file.json>`
- **Что делает:** Пропускает fetch/analyze, использует кэшированный analysis-result
- **Слои:** CLI → Filter → Format → Send

### 4. Resend сообщения
- **Команда:** `./run --resend <message.txt>`
- **Что делает:** Отправляет существующее сообщение в Telegram
- **Слои:** CLI → t2me only

---

## Golden Paths

### GP-001: Полный pipeline — fetch to Telegram
- **Триггер:** `./run --dry-run`
- **Путь:** CLI → ct-fetch → ct-schedule → ct-cognize → ct-filter → ct-format → t2me
- **Проверки:**
  - [ ] Movies fetched from kinoteatr.ru
  - [ ] Schedule enriched with showtimes
  - [ ] AI analysis produces scores
  - [ ] Filter applies taste thresholds
  - [ ] Message formatted as Telegram markdown
  - [ ] Send confirmation received

### GP-002: Replay из кэшированного analysis-result
- **Триггер:** `./run --input contracts/examples/analysis-result.sample.json`
- **Путь:** CLI → ct-filter → ct-format → t2me
- **Проверки:**
  - [ ] Fetch/schedule/cognize stages skipped
  - [ ] Filter loads cached analysis
  - [ ] Message rendered and sent

### GP-003: Resend существующего сообщения
- **Триггер:** `./run --resend message.txt`
- **Путь:** CLI → t2me only
- **Проверки:**
  - [ ] Message read from file
  - [ ] Sent to Telegram
  - [ ] Confirmation received

---

## Boundary Cases

| ID | Case | Expected Behavior |
|----|------|-------------------|
| BC-001 | Zero movies from source | Empty-state message sent |
| BC-002 | 100+ movies batch | Process within timeout |
| BC-003 | Unicode titles | No encoding errors |
| BC-004 | Long descriptions | Truncated gracefully |
| BC-005 | Scores at thresholds | Inclusive >= comparison |
| BC-006 | AI agent timeout | Pipeline aborts, artifacts preserved |
| BC-007 | Message > 4096 chars | Truncated or split |
| BC-008 | Concurrent runs | Unique RUN_IDs, no conflicts |

---

## Recovery Paths

| ID | Scenario | Recovery Action |
|----|----------|-----------------|
| RP-001 | Source unavailable | Fail fast, preserve artifacts |
| RP-002 | AI agent unavailable | Fallback chain activation |
| RP-003 | All agents fail | Abort, no silent fallback |
| RP-004 | Telegram auth error | Fail, suggest fix + resend |
| RP-005 | Stage timeout | Terminate, preserve artifacts |
| RP-006 | Contract violation | Halt, log schema error |
| RP-007 | Resend after fix | `./run --resend <message.txt>` |
| RP-008 | Dry-run resend | Validate before live send |
| RP-009 | Replay from cache | `./run --input <analyzed.json>` |
| RP-010 | Partial state | No partial send (atomic) |

---

## Тестовые данные

### Пользователи
- **Default:** `test @cinetaste.local` / `@test_user`
- **Admin:** `admin @cinetaste.local` / `@admin`

### Taste Profiles
- **Standard:** Balanced preferences (Tarkovsky, Nolan, Lynch)
- **Strict:** Very selective (only art-house)
- **Lenient:** Accepts most content

### Movie Batches
- **Mixed batch:** 4 movies with varying scores (95, 75, 45, 20)
- **All recommended:** 3 high-score movies
- **All skipped:** 2 low-score blockbusters
- **Empty:** Zero movies

### Fixtures Location
```
tests/fixtures/
├── sample_data.yaml          # All test data
└── (additional fixtures)
```

---

## Запуск тестов

```bash
# Все тесты
pytest tests/ -v

# Только integration tests (feature files)
pytest tests/features/ -v

# Только golden paths
pytest tests/features/ -k "golden" -v

# Только boundary cases
pytest tests/features/ -k "boundary" -v

# Только recovery paths
pytest tests/features/ -k "recovery" -v

# С покрытием
pytest tests/ --cov=tools --cov-report=term-missing

# Network tests (требуют подключения)
pytest tests/ -m network -v

# Dry-run pipeline test
./run --dry-run
```

---

## Структура тестов

```
tests/
├── features/
│   ├── golden_paths.feature      # 5 critical paths (@P0, @P1)
│   ├── boundary_cases.feature    # 8 boundary scenarios
│   └── recovery_paths.feature    # 10 recovery scenarios
├── fixtures/
│   └── sample_data.yaml          # Test data
├── conftest.py                   # Pytest-bdd configuration
├── test_pipeline_flow.py         # Existing flow tests
└── test_*.py                     # Tool-level tests

reports/testing/
└── coverage_analysis.md          # Coverage report
```

---

## Теги тестов

| Тег | Описание | Приоритет |
|-----|----------|-----------|
| `@critical` | Критические тесты | P0 |
| `@golden-path` | Основные сценарии | P0-P1 |
| `@happy-path` | Успешные сценарии | P0 |
| `@boundary` | Граничные случаи | P1 |
| `@recovery` | Восстановление | P1-P2 |
| `@network` | Требуют сети | - |
| `@dry-run` | Без живой отправки | - |

---

## Критерии Acceptance

### Phase 7.5 Complete When:
- [ ] 3 feature files created (golden, boundary, recovery)
- [ ] 5+ Golden Path scenarios defined
- [ ] 8+ Boundary cases defined
- [ ] 10+ Recovery paths defined
- [ ] Test fixtures documented
- [ ] Test plan written
- [ ] Coverage analysis completed
- [ ] All tests executable via pytest

---

## Метрики качества

| Метрика | Target | Измерение |
|---------|--------|-----------|
| **Golden Paths** | 3-5 | Count in golden_paths.feature |
| **Layer Coverage** | 3+ layers per path | Manual review |
| **Boundary Cases** | 8+ | Count in boundary_cases.feature |
| **Recovery Paths** | 10+ | Count in recovery_paths.feature |
| **Component Coverage** | 80%+ | See coverage_analysis.md |

---

## Риски и зависимости

### Зависимости
- kinoteatr.ru доступность (для live тестов)
- Telegram Bot API (для send тестов)
- AI агенты (kimi, gemini, qwen, pi)

### Митигация
- Использовать `--dry-run` для большинства тестов
- Mock external services в unit tests
- Кэшированные артефакты для replay тестов

---

## Changelog

### v7.5.0 — 2026-03-10
- Initial Phase 7.5 integration testing design
- Created 3 feature files with 23 total scenarios
- Defined test fixtures and sample data
- Documented test strategy and execution commands

---

*Generated by Prometheus-Vassa Plamenny, Fire-Testing Architect*  
*"One good integration test is worth a hundred unit tests"*
