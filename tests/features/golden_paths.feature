# language: en
@critical
Feature: CineTaste Pipeline Golden Paths
  As a user of CineTaste
  I want the pipeline to successfully fetch, analyze, filter, and send movie recommendations
  So that I receive personalized cinema suggestions in Telegram

  Background:
    Given the CineTaste pipeline is configured with taste profile "taste/profile.yaml"
      And the city is set to "naberezhnie-chelni"
      And Telegram bot is configured with valid credentials

  @golden-path @P0 @happy-path
  Scenario: GP-001: Full pipeline happy path — fetch to Telegram delivery
    Given today's movies are available at kinoteatr.ru for "naberezhnie-chelni"
      And the taste profile includes directors: "Tarkovsky", "Lynch", "Nolan"
      And the pipeline is executed with "./run --dry-run"
    When ct-fetch retrieves movies from the source
      And ct-schedule enriches movies with showtime data
      And ct-cognize analyzes movies against the taste profile using AI agent "auto"
      And ct-filter selects movies with score >= 60 (recommended or must_see)
      And ct-format renders the filtered list as Telegram markdown
      And t2me sends the message to Telegram (dry-run mode)
    Then the pipeline completes with exit code 0
      And at least one movie is fetched from the source
      And analyzed movies contain AI-generated scores and reasoning
      And filtered results include only movies matching taste preferences
      And the Telegram message is properly formatted with markdown
      And send-confirmation contains success: true with message_id
      And all artifacts are preserved in runs/latest/artifacts/

  @golden-path @P0 @happy-path
  Scenario: GP-002: Cached analysis replay — skip to format and send
    Given a cached analysis-result file exists at "contracts/examples/analysis-result.sample.json"
      And the file contains at least 3 analyzed movies with scores
    When the pipeline is executed with "./run --input contracts/examples/analysis-result.sample.json --dry-run"
    Then ct-fetch and ct-schedule and ct-cognize stages are skipped
      And ct-filter loads the cached analysis-result
      And ct-filter applies threshold filtering (must_see, recommended)
      And ct-format renders the message using template "telegram.md"
      And t2me sends to Telegram in dry-run mode
      And the pipeline completes successfully with exit code 0
      And send-confirmation is generated with success: true

  @golden-path @P0 @resend
  Scenario: GP-003: Resend existing message — recovery workflow
    Given a previously generated message file exists at "/tmp/test-message.txt"
      And the message contains valid Telegram markdown
    When the pipeline is executed with "./run --resend /tmp/test-message.txt --dry-run"
    Then the pipeline skips fetch/schedule/analyze/filter/format stages
      And t2me reads the message file and sends to Telegram (dry-run)
      And send-confirmation is generated with success: true
      And the pipeline exits with code 0
      And logs/sends.log is updated with resend timestamp

  @golden-path @P1 @production
  Scenario: GP-004: Production send with live Telegram delivery
    Given the pipeline is configured for production (no --dry-run flag)
      And valid Telegram credentials are set in environment
      And today's movies are available
    When the pipeline is executed with "./run"
    Then all 6 stages execute successfully
      And ct-fetch retrieves movies from kinoteatr.ru
      And ct-schedule builds showtime schedule
      And ct-cognize performs AI analysis with agent fallback chain
      And ct-filter applies taste-based filtering
      And ct-format renders Telegram-ready markdown
      And t2me sends to Telegram with live delivery (dry_run: false)
      And send-confirmation contains message_id from Telegram API
      And logs/sends.log records the successful send
      And run artifacts are saved to runs/YYYY-MM-DD/RUN_ID/

  @golden-path @P1 @agent-fallback
  Scenario: GP-005: AI agent fallback chain during cognitive analysis
    Given ct-cognize is configured with agent chain: "kimi → gemini → qwen → pi"
      And the primary agent "kimi" is unavailable or times out
    When the pipeline executes ct-cognize stage
    Then the system attempts kimi first
      And upon failure, falls back to gemini
      And gemini successfully analyzes the movies against taste profile
      And analysis-result contains valid scores and reasoning
      And the pipeline continues to ct-filter without aborting
      And no silent dry_run fallback occurs (explicit agent required)
