#!/bin/bash

# List to JSON Merge Script (Non-Overwriting)
# Merges a .list file into a JSON file preserving existing values
# Each line in .list format: key,value
# When key exists: keeps BOTH values (creates array)
# Usage: ./merge_list_json.sh input.list input.json [output.json]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if jq is installed
if ! command -v jq &> /dev/null; then
    echo -e "${RED}Error: jq is not installed.${NC}"
    echo "Please install jq:"
    echo "  Ubuntu/Debian: sudo apt-get install jq"
    echo "  Mac: brew install jq"
    exit 1
fi

# Check arguments
if [ $# -lt 2 ]; then
    echo "Usage: $0 <input.list> <input.json> [output.json]"
    echo ""
    echo "Arguments:"
    echo "  input.list   - List file with lines in format: key,value"
    echo "  input.json   - JSON file to merge into"
    echo "  output.json  - Output JSON file (optional, defaults to merged.json)"
    echo ""
    echo "Rules (Non-Overwriting Merge):"
    echo "  - Each line in .list file: key,value"
    echo "  - String before ',' becomes the key"
    echo "  - String after ',' becomes the value"
    echo "  - If key exists with SAME value: keeps single value"
    echo "  - If key exists with DIFFERENT value: keeps BOTH as array"
    echo "  - If key doesn't exist: adds new key-value pair"
    echo ""
    echo "Example .list file:"
    echo "  name,John"
    echo "  age,30"
    echo "  city,NYC"
    exit 1
fi

LIST_FILE="$1"
JSON_FILE="$2"
OUTPUT_FILE="${3:-merged.json}"

# Check if files exist
if [ ! -f "$LIST_FILE" ]; then
    echo -e "${RED}Error: List file '$LIST_FILE' not found.${NC}"
    exit 1
fi

if [ ! -f "$JSON_FILE" ]; then
    echo -e "${RED}Error: JSON file '$JSON_FILE' not found.${NC}"
    exit 1
fi

# Validate JSON file
if ! jq empty "$JSON_FILE" 2>/dev/null; then
    echo -e "${RED}Error: '$JSON_FILE' is not a valid JSON file.${NC}"
    exit 1
fi

echo -e "${YELLOW}Merging list into JSON (non-overwriting)...${NC}"
echo -e "List file: ${GREEN}$LIST_FILE${NC}"
echo -e "JSON file: ${GREEN}$JSON_FILE${NC}"
echo -e "Output: ${GREEN}$OUTPUT_FILE${NC}"
echo ""

# Start with the base JSON
cp "$JSON_FILE" "$OUTPUT_FILE"

# Process each line of the list file
LINE_COUNT=0
MERGED_COUNT=0
UPDATED_COUNT=0

while IFS= read -r line || [ -n "$line" ]; do
    # Skip empty lines
    if [ -z "$line" ]; then
        continue
    fi
    
    LINE_COUNT=$((LINE_COUNT + 1))
    
    # Split line by first comma
    if [[ "$line" =~ ^([^,]+),(.*)$ ]]; then
        KEY="${BASH_REMATCH[1]}"
        VALUE="${BASH_REMATCH[2]}"
        
        # Trim whitespace from key and value
        KEY=$(echo "$KEY" | xargs)
        VALUE=$(echo "$VALUE" | xargs)
        
        # Check if key exists in JSON
        KEY_EXISTS=$(jq --arg key "$KEY" 'has($key)' "$OUTPUT_FILE")
        
        if [ "$KEY_EXISTS" = "true" ]; then
            # Key exists - need to merge values
            EXISTING_VALUE=$(jq --arg key "$KEY" '.[$key]' "$OUTPUT_FILE")
            
            # Determine if value is numeric
            if [[ "$VALUE" =~ ^-?[0-9]+(\.[0-9]+)?$ ]]; then
                NEW_VALUE="$VALUE"
                VALUE_TYPE="number"
            else
                NEW_VALUE="\"$VALUE\""
                VALUE_TYPE="string"
            fi
            
            # Check if existing value equals new value
            if [ "$VALUE_TYPE" = "string" ]; then
                VALUE_MATCH=$(jq --arg key "$KEY" --arg val "$VALUE" '.[$key] == $val' "$OUTPUT_FILE")
            else
                VALUE_MATCH=$(jq --arg key "$KEY" --argjson val "$VALUE" '.[$key] == $val' "$OUTPUT_FILE")
            fi
            
            if [ "$VALUE_MATCH" = "true" ]; then
                # Same value - keep single value
                echo -e "${BLUE}  Kept: ${NC}$KEY = $VALUE ${YELLOW}(same value)${NC}"
            else
                # Different value - merge into array
                EXISTING_TYPE=$(jq --arg key "$KEY" '.[$key] | type' "$OUTPUT_FILE" | tr -d '"')
                
                if [ "$EXISTING_TYPE" = "array" ]; then
                    # Already an array - check if value exists in array
                    if [ "$VALUE_TYPE" = "string" ]; then
                        IN_ARRAY=$(jq --arg key "$KEY" --arg val "$VALUE" '.[$key] | contains([$val])' "$OUTPUT_FILE")
                    else
                        IN_ARRAY=$(jq --arg key "$KEY" --argjson val "$VALUE" '.[$key] | contains([$val])' "$OUTPUT_FILE")
                    fi
                    
                    if [ "$IN_ARRAY" = "true" ]; then
                        echo -e "${BLUE}  Kept: ${NC}$KEY += $VALUE ${YELLOW}(already in array)${NC}"
                    else
                        # Add to existing array
                        if [ "$VALUE_TYPE" = "string" ]; then
                            jq --arg key "$KEY" --arg val "$VALUE" '.[$key] += [$val]' "$OUTPUT_FILE" > "${OUTPUT_FILE}.tmp"
                        else
                            jq --arg key "$KEY" --argjson val "$VALUE" '.[$key] += [$val]' "$OUTPUT_FILE" > "${OUTPUT_FILE}.tmp"
                        fi
                        mv "${OUTPUT_FILE}.tmp" "$OUTPUT_FILE"
                        UPDATED_COUNT=$((UPDATED_COUNT + 1))
                        echo -e "${GREEN}  Updated: ${NC}$KEY += $VALUE ${YELLOW}(added to array)${NC}"
                    fi
                else
                    # Convert to array with both values
                    if [ "$VALUE_TYPE" = "string" ]; then
                        jq --arg key "$KEY" --arg val "$VALUE" '.[$key] = [.[$key], $val]' "$OUTPUT_FILE" > "${OUTPUT_FILE}.tmp"
                    else
                        jq --arg key "$KEY" --argjson val "$VALUE" '.[$key] = [.[$key], $val]' "$OUTPUT_FILE" > "${OUTPUT_FILE}.tmp"
                    fi
                    mv "${OUTPUT_FILE}.tmp" "$OUTPUT_FILE"
                    UPDATED_COUNT=$((UPDATED_COUNT + 1))
                    echo -e "${GREEN}  Merged: ${NC}$KEY = [existing, $VALUE] ${YELLOW}(created array)${NC}"
                fi
            fi
        else
            # Key doesn't exist - add new key-value pair
            if [[ "$VALUE" =~ ^-?[0-9]+(\.[0-9]+)?$ ]]; then
                jq --arg key "$KEY" --argjson val "$VALUE" '. + {($key): $val}' "$OUTPUT_FILE" > "${OUTPUT_FILE}.tmp"
            else
                jq --arg key "$KEY" --arg val "$VALUE" '. + {($key): $val}' "$OUTPUT_FILE" > "${OUTPUT_FILE}.tmp"
            fi
            mv "${OUTPUT_FILE}.tmp" "$OUTPUT_FILE"
            MERGED_COUNT=$((MERGED_COUNT + 1))
            echo -e "${BLUE}  Added: ${NC}$KEY = $VALUE"
        fi
    else
        echo -e "${YELLOW}  Warning: Skipping invalid line $LINE_COUNT (no comma found): $line${NC}"
    fi
done < "$LIST_FILE"

echo ""
echo -e "${GREEN}✓ Merge completed successfully${NC}"
echo -e "Lines processed: ${GREEN}$LINE_COUNT${NC}"
echo -e "New keys added: ${GREEN}$MERGED_COUNT${NC}"
echo -e "Existing keys merged: ${GREEN}$UPDATED_COUNT${NC}"
echo ""
echo -e "Result preview:"
jq '.' "$OUTPUT_FILE" | head -n 30
