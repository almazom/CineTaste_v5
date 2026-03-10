# language: en
@boundary
Feature: Boundary Cases and Limits
  As a CineTaste user
  I want the pipeline to handle edge cases and boundary conditions gracefully
  So that the system remains stable under extreme or unusual inputs

  Background:
    Given the pipeline is configured with default taste profile
      And the city is set to "naberezhnie-chelni"

  @boundary @P1 @empty-input
  Scenario: BC-001: Zero movies available from source
    Given kinoteatr.ru returns an empty movie list for today
    When ct-fetch executes successfully
    Then the pipeline continues with 0 movies
      And ct-schedule produces movie-schedule with empty movies array
      And ct-cognize produces analysis-result with 0 analyzed movies
      And ct-filter produces filter-result with 0 filtered movies
      And ct-format renders a message indicating "No movies today"
      And t2me sends the empty-state message to Telegram
      And the pipeline completes with exit code 0

  @boundary @P1 @large-batch
  Scenario: BC-002: Large movie batch processing (100+ movies)
    Given the source returns 150 movies for today
    When ct-fetch retrieves all 150 movies
      And ct-schedule processes the full batch
      And ct-cognize analyzes all movies against taste profile
    Then the pipeline completes within timeout (720 seconds)
      And memory usage remains within acceptable limits
      And all 150 movies are analyzed with AI scores
      And ct-filter correctly applies threshold filtering
      And the final message includes top recommendations only

  @boundary @P1 @special-chars
  Scenario: BC-003: Movie titles with special characters and Unicode
    Given the source includes movies with titles:
      | Title                              |
      | "Сталкер" (Russian)                |
      | "L'Année dernière à Marienbad"     |
      | "8½"                               |
      | "C'est la vie"                     |
      | "Film with \"quotes\" and 'apostrophes'" |
    When ct-fetch retrieves these movies
      And ct-cognize analyzes them
      And ct-format renders the message
    Then all titles are preserved without corruption
      And the Telegram message displays correctly
      And no JSON encoding errors occur
      And markdown special characters are properly escaped

  @boundary @P1 @long-content
  Scenario: BC-004: Extremely long movie descriptions
    Given a movie has a description exceeding 2000 characters
    When ct-cognize generates analysis for this movie
      And ct-format includes it in the message
    Then the description is truncated to fit Telegram limits
      And the truncated text ends with "..."
      And the message still includes all essential info (title, time, cinema)
      And no message truncation errors occur

  @boundary @P1 @score-threshold
  Scenario: BC-005: Movies at exact threshold boundaries
    Given analyzed movies with scores:
      | Movie              | Score |
      | "Must See Film"    | 85    |
      | "Borderline Good"  | 60    |
      | "Just Below"       | 59    |
      | "Exactly Zero"     | 0     |
    When ct-filter applies thresholds (must_see: 85, recommended: 60)
    Then "Must See Film" (85) is included as must_see
      And "Borderline Good" (60) is included as recommended
      And "Just Below" (59) is excluded
      And "Exactly Zero" (0) is excluded
      And threshold comparisons use >= (inclusive)

  @boundary @P1 @timeout
  Scenario: BC-006: AI agent timeout during cognitive analysis
    Given the AI agent takes longer than pipeline timeout (720s)
    When ct-cognize executes with --agent auto
    Then the stage times out after 720 seconds
      And the pipeline aborts with exit code 124
      And failure artifacts are preserved in logs/failed_*/
      And RECOVER.md provides recovery instructions
      And no partial send occurs

  @boundary @P1 @telegram-limit
  Scenario: BC-007: Message exceeds Telegram character limit
    Given filtered results would generate a 5000-character message
      And Telegram message limit is 4096 characters
    When ct-format renders the message
    Then the message is truncated or split appropriately
      And the most important recommendations are included first
      And lower-priority movies are omitted if needed
      And the final message is under 4096 characters
      And t2me sends without length errors

  @boundary @P1 @concurrent-runs
  Scenario: BC-008: Concurrent pipeline executions
    Given two pipeline instances are started simultaneously
    When both execute "./run --dry-run" at the same time
    Then each run gets a unique RUN_ID timestamp
      And artifacts are saved to separate runs/RUN_ID/ directories
      And no file locking conflicts occur
      And both runs complete successfully
