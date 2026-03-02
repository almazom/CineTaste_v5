# 🔧 Troubleshooting — CineTaste v5

## Common Issues

### 1. Contract Validation Fails

**Symptom:** "Contract violation: movie-batch.schema.json field X"

**Causes:**
- Missing required field
- Wrong type
- Extra field (additionalProperties: false)

**Fix:**
```bash
# Check input against schema
python3 -c "
import json, jsonschema
data = json.load(open('movies.json'))
schema = json.load(open('contracts/movie-batch.schema.json'))
jsonschema.validate(data, schema)
"
```

### 2. AI Agent Not Working

**Symptom:** ct-analyze fails or returns empty

**Check:**
```bash
# Test pi agent
pi -p "1+1"  # Should return "2"

# Check taste profile
cat taste/profile.yaml
```

### 3. Telegram Send Fails

**Symptom:** t2me returns error

**Check:**
```bash
# Verify authorization
t2me status

# Re-authorize if needed
t2me auth
```

### 4. No Movies Matched

**Symptom:** "0 movies matched taste profile"

**Causes:**
- Taste profile too restrictive
- No good movies today
- AI analysis failed

**Fix:**
```bash
# Check what was analyzed
cat /tmp/ct-analyze/analyzed.json | jq '.analyzed[].recommendation'

# Lower threshold
./run --dry-run  # Review scores
# Edit taste/profile.yaml thresholds
```

## Debug Mode

```bash
# Verbose output
./run --verbose --dry-run

# Check intermediate files
ls -la /tmp/ct-*/
```

## Log Files

| Log | Location | Contents |
|-----|----------|----------|
| Sends | `logs/sends.log` | Successful deliveries |
| Errors | `logs/errors.log` | Failures with timestamps |
| Failed messages | `logs/failed_*.txt` | Preserved for resend |

## Recovery

```bash
# Resend failed message
./run --resend logs/failed_20260302_103000.txt

# Re-run from cached analysis
./run --input /tmp/ct-analyze/analyzed.json
```

## Getting Help

1. Check this file
2. Read PROTOCOL.json for system topology
3. Check tool MANIFEST.json for CLI options
4. Run with --dry-run to isolate issue

---
*Last updated: 2026-03-02*
