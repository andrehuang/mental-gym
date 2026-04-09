#!/bin/bash
# Mental Gym auto-suggest hook
# Triggered by PostToolUse on Write|Edit
# Checks if the changed file is wiki/research-related and suggests training

MENTAL_GYM_DIR="$(cd "$(dirname "$0")/.." 2>/dev/null && pwd)"

# Read hook input from stdin
INPUT=$(cat)

# Extract the file path from the tool input
FILE_PATH=$(echo "$INPUT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
tool_input = data.get('tool_input', {})
print(tool_input.get('file_path', ''))
" 2>/dev/null)

if [ -z "$FILE_PATH" ]; then
    exit 0
fi

# Only trigger for wiki, papers, docs, and draft files
case "$FILE_PATH" in
    */wiki/*|*/docs/*|*/papers/*|*draft*|*paper*)
        ;;
    *.md|*.tex)
        ;;
    *)
        exit 0
        ;;
esac

# Run mental-gym suggest (silently fail if not installed/initialized)
if [ -f "$MENTAL_GYM_DIR/mental_gym.yaml" ] && [ -f "$MENTAL_GYM_DIR/.venv/bin/mental-gym" ]; then
    SUGGESTION=$(cd "$MENTAL_GYM_DIR" && .venv/bin/mental-gym suggest --changed-file "$FILE_PATH" 2>/dev/null)
    if [ -n "$SUGGESTION" ]; then
        # Output as system message for Claude to see
        echo "$SUGGESTION"
    fi
fi

exit 0
