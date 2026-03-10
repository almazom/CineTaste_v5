# language: en
@recovery
Feature: Recovery Paths and Error Handling
  As a CineTaste user
  I want the pipeline to handle failures gracefully and provide recovery options
  So that I can resume from failures without losing progress

  Background:
    Given the pipeline is configured with default settings
      And run logging is enabled

  @recovery @P1 @source-unavailable
  Scenario: RP-001: Source website unavailable — graceful failure
    Given kinoteatr.ru is temporarily unavailable (HTTP 503)
    When ct-fetch attempts to retrieve movies
    Then ct-fetch fails with appropriate error message
      And the pipeline halts immediately (no partial send)
      And failure artifacts are preserved in logs/failed_*/
      And RECOVER.md is generated with recovery instructions
      And error is logged to logs/errors.log
      And the pipeline exits with non-zero code

  @recovery @P1 @db-connection
  Scenario: RP-002: AI agent unavailable — fallback chain activation
    Given the primary AI agent "kimi" is unavailable
      And the fallback chain is: kimi → gemini → qwen → pi
    When ct-cognize executes with --agent auto
    Then the system attempts kimi first
      And upon failure, automatically falls back to gemini
      And gemini successfully completes the analysis
      And analysis-result is generated with valid scores
      And the pipeline continues to ct-filter
      And logs indicate which agent was used

  @recovery @P2 @all-agents-fail
  Scenario: RP-003: All AI agents fail — pipeline abort
    Given all AI agents (kimi, gemini, qwen, pi) are unavailable
    When ct-cognize executes with --agent auto
    Then each agent in the fallback chain fails
      And the pipeline aborts (no silent dry_run fallback)
      And an explicit error is logged indicating all agents failed
      And failure artifacts are preserved
      And RECOVER.md suggests retrying later or with specific agent

  @recovery @P1 @telegram-error
  Scenario: RP-004: Telegram send failure — auth error
    Given Telegram credentials are invalid or expired
      And all previous stages completed successfully
    When t2me attempts to send the message
    Then t2me returns an error status
      And send-confirmation contains success: false
      And the pipeline validates send-confirmation and fails
      And failure artifacts include the rendered message.txt
      And RECOVER.md suggests: "./run --resend <message.txt>" after fixing auth
      And logs/sends.log does NOT record this as a successful send

  @recovery @P1 @timeout
  Scenario: RP-005: Stage timeout — graceful termination
    Given a stage (e.g., ct-cognize) exceeds timeout (720s)
    When the stage is executing
    Then the stage is terminated after 720 seconds
      And the pipeline exits with code 124
      And failure artifacts are preserved in logs/failed_*/
      And RECOVER.md suggests increasing timeout or retrying
      And no partial send occurs

  @recovery @P2 @contract-violation
  Scenario: RP-006: Contract violation — invalid JSON schema
    Given ct-fetch produces output that violates movie-batch schema
    When the output is validated against the contract
    Then the pipeline detects the schema violation
      And the pipeline halts before ct-schedule
      And the error specifies which schema field failed
      And failure artifacts include the invalid JSON
      And RECOVER.md suggests inspecting the source or ct-fetch logic

  @recovery @P2 @resend-retry
  Scenario: RP-006: Resend after temporary Telegram outage
    Given a previous run failed at t2me stage
      And the message.txt artifact exists in logs/failed_*/
      And Telegram service is now available
    When the user executes "./run --resend logs/failed_*/message.txt"
    Then the pipeline skips to t2me stage
      And the message is sent successfully
      And logs/sends.log records the successful resend
      And the run is marked as successful

  @recovery @P2 @dry-run-resend
  Scenario: RP-008: Dry-run resend validates before live send
    Given a preserved message from a failed dry-run
    When the user executes "./run --dry-run --resend logs/failed_*/message.txt"
    Then t2me validates the send in dry-run mode
      And send-confirmation shows dry_run: true
      And no live Telegram message is sent
      And the user can inspect the confirmation payload
      And the user can then run without --dry-run for live send

  @recovery @P2 @input-replay
  Scenario: RP-009: Replay from cached analysis-result
    Given a previous run failed after ct-cognize completed
      And analyzed.json exists in artifacts
    When the user executes "./run --input runs/latest/artifacts/analyzed.json"
    Then ct-fetch, ct-schedule, and ct-cognize are skipped
      And ct-filter loads the cached analysis
      And the pipeline continues from ct-filter onward
      And the run completes successfully if no further errors

  @recovery @P1 @partial-state
  Scenario: RP-010: No partial send on intermediate failure
    Given ct-format completed successfully
      And t2me fails during send
    When the pipeline fails
    Then no Telegram message was sent (atomic send)
      And message.txt is preserved in failure artifacts
      And RECOVER.md provides resend command
      And logs/sends.log does not contain this run
      And the user can safely retry without duplicate sends
