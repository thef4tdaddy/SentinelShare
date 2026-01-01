#!/bin/bash
# SentinelShare File Size Audit Script
# Identifies files that exceed the recommended line count threshold.

THRESHOLD=${1:-500}
PROJECT_ROOT=$(pwd)
LOG_FILE="file_sizes.log"

echo "🔍 Auditing file sizes (Threshold: $THRESHOLD lines)..." > "$LOG_FILE"
echo "------------------------------------------------" >> "$LOG_FILE"

# Find files, excluding common non-source directories
# Target: .py, .svelte, .ts, .js
find . -type f \( -name "*.py" -o -name "*.svelte" -o -name "*.ts" -o -name "*.js" \) \
    -not -path "*/node_modules/*" \
    -not -path "*/venv/*" \
    -not -path "*/.git/*" \
    -not -path "*/dist/*" \
    -not -path "*/.svelte-kit/*" \
    -not -path "*/package-lock.json" \
    -not -path "*/public/*" | while read -r file; do
    
    # Count lines
    LINES=$(wc -l < "$file" | tr -d ' ')
    
    if [ "$LINES" -gt "$THRESHOLD" ]; then
        # Strip leading ./ for cleaner report
        CLEAN_PATH=${file#./}
        echo "OVERSIZED_FILE:$CLEAN_PATH:$LINES" >> "$LOG_FILE"
        echo "⚠️  $CLEAN_PATH: $LINES lines" >> "$LOG_FILE"
    fi
done

# Check if any oversized files were found
if grep -q "OVERSIZED_FILE" "$LOG_FILE"; then
    COUNT=$(grep -c "OVERSIZED_FILE" "$LOG_FILE")
    echo "------------------------------------------------" >> "$LOG_FILE"
    echo "❌ Audit failed: Found $COUNT oversized files." >> "$LOG_FILE"
    # Don't exit with non-zero yet, we want the health check to continue and report it
else
    echo "✅ Audit passed: No files exceed the threshold." >> "$LOG_FILE"
fi

cat "$LOG_FILE"
