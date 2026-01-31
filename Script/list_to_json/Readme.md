# List to JSON 转换工具

这是一个将 list 格式的规则文件转换为 JSON 格式的 Python 脚本。

## 功能特点

- ✅ 从 URL 自动下载 list 文件
- ✅ 自动检查文件有效性
- ✅ 转换规则到 JSON 格式
- ✅ 在同目录输出同名的 JSON 文件
- ✅ 详细的转换统计信息
- ✅ 支持自定义输出目录和版本号

## 安装依赖

```bash
pip install requests
```

## 使用方法

### 基本用法

```bash
python list_to_json.py <list文件URL>
```

示例：
```bash
python list_to_json.py https://example.com/rules.list
```

这将：
1. 下载 `rules.list` 文件到当前目录
2. 检查文件有效性
3. 转换并生成 `rules.json` 文件到当前目录

### 指定版本号

```bash
python list_to_json.py <list文件URL> <版本号>
```

示例：
```bash
python list_to_json.py https://example.com/rules.list 3
```

### 指定输出目录

```bash
python list_to_json.py <list文件URL> <版本号> <输出目录>
```

示例：
```bash
python list_to_json.py https://example.com/rules.list 2 ./output
```

## 转换规则

脚本支持以下类型的规则转换：

| List 格式 | JSON 字段 | 说明 |
|-----------|-----------|------|
| `DOMAIN,example.com` | `domain` | 精确域名匹配 |
| `DOMAIN-KEYWORD,keyword` | `domain_keyword` | 域名关键字匹配 |
| `DOMAIN-SUFFIX,example.com` | `domain_suffix` | 域名后缀匹配 |

**注意**：其他类型的规则（如 `IP-CIDR`、`USER-AGENT`、`PROCESS-NAME` 等）将被忽略。

## 输入文件格式示例

```
DOMAIN,voice.telephony.goog
DOMAIN-SUFFIX,0emm.com
DOMAIN-SUFFIX,googledrive.com
DOMAIN-KEYWORD,appspot
DOMAIN-KEYWORD,google
IP-CIDR,172.110.32.0/21,no-resolve
USER-AGENT,Google.Drive*
```

## 输出文件格式示例

```json
{
  "rules": [
    {
      "domain": [
        "voice.telephony.goog"
      ]
    },
    {
      "domain_keyword": [
        "appspot",
        "google"
      ]
    },
    {
      "domain_suffix": [
        "0emm.com",
        "googledrive.com"
      ]
    }
  ],
  "version": 2
}
```

## 输出信息

脚本运行时会显示：
- 下载进度
- 文件检查结果（总行数和有效规则数）
- 转换统计：
  - DOMAIN 规则数量
  - DOMAIN-KEYWORD 规则数量
  - DOMAIN-SUFFIX 规则数量
  - 已忽略的规则数量
- 最终输出文件路径

## 示例输出

```
输出目录: ./output
List文件: rules.list
JSON文件: rules.json
--------------------------------------------------
正在下载: https://example.com/rules.list
下载成功: ./output/rules.list
--------------------------------------------------
文件检查通过: 共 23 行, 23 条有效规则
--------------------------------------------------

转换统计:
  - DOMAIN: 1 条
  - DOMAIN-KEYWORD: 5 条
  - DOMAIN-SUFFIX: 4 条
  - 已忽略: 13 条

成功: 已生成 ./output/rules.json
--------------------------------------------------
✓ 完成! JSON文件已保存到: ./output/rules.json
```

## 错误处理

脚本会处理以下错误情况：
- URL 下载失败
- 文件读取错误
- 文件为空或格式错误
- JSON 写入失败

## 许可证

MIT License
