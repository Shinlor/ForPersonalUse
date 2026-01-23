#!/bin/bash

################################################################################
# JSON文件合并脚本
################################################################################
#
# 功能说明:
#   本脚本用于合并多个JSON文件中的rules数组,将相同key的数组值合并并去重。
#   自动生成两个输出文件:完整版和不含IP地址的版本。
#
# 使用方法:
#   ./merge_json.sh file1.json file2.json [file3.json ...] [-o output.json]
#
# 参数说明:
#   file1.json file2.json ...  要合并的JSON文件(至少需要1个文件)
#   -o, --output               指定输出文件名(可选,默认为merged.json)
#
# 输出文件:
#   1. 完整版: 指定的输出文件名(如: output.json)
#      包含所有字段: domain, domain_keyword, domain_suffix, ip_cidr
#   
#   2. 无IP版: 文件名后加-no-ip(如: output-no-ip.json)
#      不包含ip_cidr字段,只保留其他字段
#
# 使用示例:
#   # 合并两个文件,输出到merged.json
#   ./merge_json.sh Netflix.json YouTube.json
#
#   # 合并多个文件,指定输出文件名
#   ./merge_json.sh Netflix.json YouTube.json Disney.json -o output.json
#
#   # 使用通配符合并所有JSON文件
#   ./merge_json.sh *.json -o all_merged.json
#
# 合并规则:
#   - 只保留rules字段,忽略其他所有字段(如version等)
#   - rules数组中具有相同key的对象会被合并
#   - 相同key下的数组值会合并并自动去重
#   - 如: 两个文件都有domain字段,会合并为一个domain对象,包含所有域名
#
# JSON文件格式要求:
#   输入文件必须符合以下格式:
#   {
#     "rules": [
#       {"domain": ["example.com", "test.com"]},
#       {"domain_keyword": ["keyword1"]},
#       {"domain_suffix": [".example.com"]},
#       {"ip_cidr": ["192.168.1.0/24"]}
#     ],
#     "version": 2  // 可选,会被忽略
#   }
#
# 依赖要求:
#   - jq: JSON处理工具(必需)
#     Ubuntu/Debian: sudo apt-get install jq
#     CentOS/RHEL:   sudo yum install jq
#     macOS:         brew install jq
#
# 注意事项:
#   1. 确保所有输入文件都是有效的JSON格式
#   2. 输入文件必须包含rules字段,否则会被跳过并给出警告
#   3. 文件名可以包含空格,脚本会正确处理
#   4. 如果输出文件已存在,会被覆盖
#   5. 合并后的数组会自动按字母顺序排序并去重
#   6. 脚本会保留JSON的格式化输出,便于阅读
#
# 错误处理:
#   - 如果jq未安装,脚本会提示安装方法并退出
#   - 如果输入文件不存在,会显示错误并退出
#   - 如果JSON格式无效,会显示错误并退出
#   - 如果rules字段缺失,会显示警告但继续处理其他文件
#
# 作者: Claude
# 版本: 1.0
# 更新日期: 2026-01-23
#
################################################################################

# JSON文件合并脚本
# 用法: ./merge_json.sh file1.json file2.json [file3.json ...] -o output.json

# 检查是否安装了jq
if ! command -v jq &> /dev/null; then
    echo "错误: 需要安装jq工具"
    echo "请使用以下命令安装:"
    echo "  Ubuntu/Debian: sudo apt-get install jq"
    echo "  CentOS/RHEL: sudo yum install jq"
    echo "  macOS: brew install jq"
    exit 1
fi

# 解析参数
OUTPUT_FILE="merged.json"
INPUT_FILES=()

while [[ $# -gt 0 ]]; do
    case $1 in
        -o|--output)
            OUTPUT_FILE="$2"
            shift 2
            ;;
        *)
            INPUT_FILES+=("$1")
            shift
            ;;
    esac
done

# 检查是否有输入文件
if [ ${#INPUT_FILES[@]} -eq 0 ]; then
    echo "用法: $0 file1.json file2.json [file3.json ...] [-o output.json]"
    echo ""
    echo "选项:"
    echo "  -o, --output    指定输出文件名 (默认: merged.json)"
    echo ""
    echo "输出文件:"
    echo "  - 完整文件: <指定的文件名>"
    echo "  - 无IP文件: <文件名>-no-ip.json (不包含ip_cidr字段)"
    echo ""
    echo "合并规则:"
    echo "  - 只保留rules字段,忽略其他所有字段(如version等)"
    echo "  - rules数组中相同key的对象会被合并"
    echo "  - 相同key的数组值会合并并去重"
    echo ""
    echo "示例:"
    echo "  $0 a.json b.json -o result.json"
    echo "  将生成: result.json 和 result-no-ip.json"
    exit 1
fi

# 检查所有输入文件是否存在
for file in "${INPUT_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo "错误: 文件不存在: $file"
        exit 1
    fi
    
    # 检查JSON格式是否有效
    if ! jq empty "$file" 2>/dev/null; then
        echo "错误: 无效的JSON文件: $file"
        exit 1
    fi
    
    # 检查是否包含rules字段
    if ! jq -e '.rules' "$file" >/dev/null 2>&1; then
        echo "警告: 文件 $file 不包含 rules 字段,将被跳过"
    fi
done

echo "开始合并 ${#INPUT_FILES[@]} 个JSON文件..."
echo "输入文件: ${INPUT_FILES[*]}"

# 执行合并
echo "执行jq命令..."
RESULT=$(jq -s '{
  rules: (
    map(select(.rules != null) | .rules) | add | 
    if . == null then [] 
    else group_by(keys[0]) | map(
      (.[0] | keys[0]) as $k | 
      {($k): (map(.[$k]) | add | unique)}
    )
    end
  )
}' "${INPUT_FILES[@]}" 2>&1)
JQ_EXIT_CODE=$?

echo "jq退出码: $JQ_EXIT_CODE"

# 检查合并是否成功
if [ $JQ_EXIT_CODE -ne 0 ]; then
    echo "错误: JSON合并失败"
    echo "jq输出: $RESULT"
    exit 1
fi

# 输出结果
echo "$RESULT" | jq '.' > "$OUTPUT_FILE"

if [ $? -eq 0 ]; then
    echo "✓ 完整文件合并完成! 输出文件: $OUTPUT_FILE"
    
    # 生成无IP版本的文件名
    FILENAME="${OUTPUT_FILE%.*}"
    EXTENSION="${OUTPUT_FILE##*.}"
    if [ "$FILENAME" = "$OUTPUT_FILE" ]; then
        # 没有扩展名
        NO_IP_FILE="${OUTPUT_FILE}-no-ip"
    else
        # 有扩展名
        NO_IP_FILE="${FILENAME}-no-ip.${EXTENSION}"
    fi
    
    # 生成不包含ip_cidr的版本
    echo ""
    echo "正在生成无IP版本..."
    NO_IP_RESULT=$(echo "$RESULT" | jq '.rules |= map(select(has("ip_cidr") | not))' 2>&1)
    
    if [ $? -eq 0 ]; then
        echo "$NO_IP_RESULT" > "$NO_IP_FILE"
        if [ $? -eq 0 ]; then
            echo "✓ 无IP文件生成完成! 输出文件: $NO_IP_FILE"
        else
            echo "⚠ 警告: 无IP文件写入失败"
            NO_IP_FILE=""
        fi
    else
        echo "⚠ 警告: 无IP文件生成失败: $NO_IP_RESULT"
        NO_IP_FILE=""
    fi
    
    echo ""
    echo "合并的文件: ${INPUT_FILES[*]}"
    echo ""
    echo "验证合并结果:"
    echo "完整文件:"
    echo "  - 文件大小: $(wc -c < "$OUTPUT_FILE") 字节"
    if command -v jq &> /dev/null; then
        RULES_COUNT=$(jq '.rules | length' "$OUTPUT_FILE")
        echo "  - rules数组元素数: $RULES_COUNT"
    fi
    
    if [ -f "$NO_IP_FILE" ] && [ -n "$NO_IP_FILE" ]; then
        echo "无IP文件:"
        echo "  - 文件大小: $(wc -c < "$NO_IP_FILE") 字节"
        if command -v jq &> /dev/null; then
            NO_IP_RULES_COUNT=$(jq '.rules | length' "$NO_IP_FILE" 2>/dev/null)
            if [ -n "$NO_IP_RULES_COUNT" ]; then
                echo "  - rules数组元素数: $NO_IP_RULES_COUNT"
            fi
        fi
    fi
else
    echo "错误: 写入输出文件失败"
    exit 1
fi
