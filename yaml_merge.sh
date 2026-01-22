#!/bin/bash

# YAML Merge Script (Non-Overwriting)
# Merges two YAML files preserving conflicting values from both files
# When the same key exists with different values, both are kept
# Usage: ./yaml_merge.sh base.yaml merge.yaml [output.yaml]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if yq is installed
if ! command -v yq &> /dev/null; then
    echo -e "${RED}Error: yq is not installed.${NC}"
    echo "Please install yq: https://github.com/mikefarah/yq"
    echo "  Ubuntu/Debian: sudo snap install yq"
    echo "  Mac: brew install yq"
    exit 1
fi

# Check arguments
if [ $# -lt 2 ]; then
    echo "Usage: $0 <file1.yaml> <file2.yaml> [output.yaml]"
    echo ""
    echo "Arguments:"
    echo "  file1.yaml    - First YAML file"
    echo "  file2.yaml    - Second YAML file"
    echo "  output.yaml   - Output file (optional, prints to stdout if not specified)"
    echo ""
    echo "Merge Strategy (Non-Overwriting):"
    echo "  - When same key exists with SAME value: keep single value"
    echo "  - When same key exists with DIFFERENT values: keep BOTH (array)"
    echo "  - Unique keys from both files are preserved"
    echo "  - Nested objects are merged recursively"
    exit 1
fi

FILE1="$1"
FILE2="$2"
OUTPUT_FILE="${3:-}"

# Check if files exist
if [ ! -f "$FILE1" ]; then
    echo -e "${RED}Error: File '$FILE1' not found.${NC}"
    exit 1
fi

if [ ! -f "$FILE2" ]; then
    echo -e "${RED}Error: File '$FILE2' not found.${NC}"
    exit 1
fi

echo -e "${YELLOW}Merging YAML files (non-overwriting)...${NC}"
echo -e "File 1: ${GREEN}$FILE1${NC}"
echo -e "File 2: ${GREEN}$FILE2${NC}"
echo ""

# Create a temporary Python script to handle the merge
TEMP_SCRIPT=$(mktemp)
cat > "$TEMP_SCRIPT" << 'PYTHON_EOF'
import yaml
import sys
from collections import OrderedDict

def merge_yaml(base, overlay):
    """
    Merge two YAML structures without overwriting.
    When keys conflict with different values, keep both as array.
    """
    if isinstance(base, dict) and isinstance(overlay, dict):
        result = base.copy()
        for key, overlay_value in overlay.items():
            if key in result:
                base_value = result[key]
                if base_value == overlay_value:
                    # Same value, keep single copy
                    continue
                elif isinstance(base_value, dict) and isinstance(overlay_value, dict):
                    # Both are dicts, merge recursively
                    result[key] = merge_yaml(base_value, overlay_value)
                elif isinstance(base_value, list) and isinstance(overlay_value, list):
                    # Both are lists, combine and deduplicate
                    result[key] = base_value + [item for item in overlay_value if item not in base_value]
                else:
                    # Different values, keep both as array
                    if isinstance(base_value, list):
                        if overlay_value not in base_value:
                            result[key] = base_value + [overlay_value]
                    else:
                        result[key] = [base_value, overlay_value]
            else:
                # New key, add it
                result[key] = overlay_value
        return result
    elif isinstance(base, list) and isinstance(overlay, list):
        # Combine lists and deduplicate
        return base + [item for item in overlay if item not in base]
    else:
        # For non-dict/list types, if different, return both as list
        if base == overlay:
            return base
        else:
            return [base, overlay]

try:
    with open(sys.argv[1], 'r') as f1:
        data1 = yaml.safe_load(f1) or {}
    
    with open(sys.argv[2], 'r') as f2:
        data2 = yaml.safe_load(f2) or {}
    
    merged = merge_yaml(data1, data2)
    
    output = yaml.dump(merged, default_flow_style=False, sort_keys=False, allow_unicode=True)
    
    if len(sys.argv) > 3:
        with open(sys.argv[3], 'w') as f:
            f.write(output)
    else:
        print(output, end='')
        
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
    sys.exit(1)
PYTHON_EOF

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: python3 is not installed.${NC}"
    echo "This script requires Python 3 with PyYAML."
    rm "$TEMP_SCRIPT"
    exit 1
fi

# Check if PyYAML is installed
if ! python3 -c "import yaml" 2>/dev/null; then
    echo -e "${RED}Error: PyYAML is not installed.${NC}"
    echo "Install it with: pip3 install pyyaml"
    rm "$TEMP_SCRIPT"
    exit 1
fi

# Run the merge
if [ -n "$OUTPUT_FILE" ]; then
    python3 "$TEMP_SCRIPT" "$FILE1" "$FILE2" "$OUTPUT_FILE"
    echo -e "${GREEN}✓ Merged YAML written to: $OUTPUT_FILE${NC}"
else
    python3 "$TEMP_SCRIPT" "$FILE1" "$FILE2"
fi

# Cleanup
rm "$TEMP_SCRIPT"
