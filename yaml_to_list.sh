#!/bin/bash

# YAML Payload Extractor
# Extracts the 'payload' key from a YAML file and outputs line by line to .list file
# Usage: ./extract_payload.sh input.yaml [output.list]
# Requirements: yq

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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
if [ $# -lt 1 ]; then
    echo "Usage: $0 <input.yaml> [output.list]"
    echo ""
    echo "Arguments:"
    echo "  input.yaml   - YAML file containing 'payload' key"
    echo "  output.list  - Output .list file (optional, defaults to payload.list)"
    echo ""
    echo "Examples:"
    echo "  $0 config.yaml"
    echo "  $0 config.yaml output.list"
    echo "  $0 data.yaml custom_name.list"
    exit 1
fi

INPUT_FILE="$1"
OUTPUT_FILE="${2:-payload.list}"

# Ensure output file has .list extension
if [[ ! "$OUTPUT_FILE" =~ \.list$ ]]; then
    OUTPUT_FILE="${OUTPUT_FILE}.list"
fi

# Check if input file exists
if [ ! -f "$INPUT_FILE" ]; then
    echo -e "${RED}Error: Input file '$INPUT_FILE' not found.${NC}"
    exit 1
fi

# Check if 'payload' key exists in the YAML file
if ! yq eval '.payload' "$INPUT_FILE" | grep -qv '^null$'; then
    echo -e "${RED}Error: 'payload' key not found in '$INPUT_FILE'.${NC}"
    exit 1
fi

echo -e "${YELLOW}Extracting 'payload' from YAML...${NC}"
echo -e "Input: ${GREEN}$INPUT_FILE${NC}"
echo -e "Output: ${GREEN}$OUTPUT_FILE${NC}"
echo ""

# Extract payload and write to .list file
# Handle both array and scalar values
PAYLOAD_TYPE=$(yq eval '.payload | type' "$INPUT_FILE")

case "$PAYLOAD_TYPE" in
    "!!seq")
        # Payload is an array - output each element on a new line
        yq eval '.payload[]' "$INPUT_FILE" > "$OUTPUT_FILE"
        ;;
    "!!str"|"!!int"|"!!float"|"!!bool")
        # Payload is a scalar value - output as single line
        yq eval '.payload' "$INPUT_FILE" > "$OUTPUT_FILE"
        ;;
    "!!map")
        # Payload is a map/object - output each value on a new line
        yq eval '.payload | to_entries | .[] | .value' "$INPUT_FILE" > "$OUTPUT_FILE"
        ;;
    *)
        echo -e "${RED}Error: Unsupported payload type: $PAYLOAD_TYPE${NC}"
        exit 1
        ;;
esac

# Count lines written
LINE_COUNT=$(wc -l < "$OUTPUT_FILE")

echo -e "${GREEN}✓ Successfully extracted payload${NC}"
echo -e "Lines written: ${GREEN}$LINE_COUNT${NC}"
echo ""
echo -e "Preview of ${YELLOW}$OUTPUT_FILE${NC}:"
head -n 10 "$OUTPUT_FILE"
if [ "$LINE_COUNT" -gt 10 ]; then
    echo "... (showing first 10 of $LINE_COUNT lines)"
fi
