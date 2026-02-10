#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
List to YAML Converter for Mihomo/Clash Rules
从指定URL下载.list文件并转换为.yaml格式
"""

import os
import re
import sys
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from typing import Dict, List, Tuple


# 支持的规则类型（YAML格式支持的类型）
SUPPORTED_RULE_TYPES = {
    'DOMAIN-SUFFIX',
    'DOMAIN-KEYWORD',
    'IP-CIDR',
    'IP-CIDR6',
    'DOMAIN',
    'DOMAIN-SET',
    'GEOIP',
    'IP-ASN',
}

# 不支持的规则类型（需要过滤掉）
UNSUPPORTED_RULE_TYPES = {
    'USER-AGENT',
    'URL-REGEX',
    'PROCESS-NAME',
}


def download_file(url: str) -> Tuple[str, str]:
    """
    下载文件
    
    Args:
        url: 文件URL
    
    Returns:
        (文件内容, 文件名)
    """
    print(f"📥 正在下载: {url}")
    
    try:
        # 添加User-Agent以避免被某些服务器拒绝
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        request = Request(url, headers=headers)
        
        with urlopen(request, timeout=30) as response:
            content = response.read().decode('utf-8')
            
            # 从URL中提取文件名
            filename = url.split('/')[-1]
            
            print(f"✓ 下载成功: {filename} ({len(content)} 字节)")
            return content, filename
    
    except HTTPError as e:
        print(f"✗ HTTP错误 {e.code}: {url}")
        raise
    except URLError as e:
        print(f"✗ URL错误: {e.reason}")
        raise
    except Exception as e:
        print(f"✗ 下载失败: {e}")
        raise


def parse_list_file(content: str, filename: str) -> Dict:
    """
    解析.list文件内容
    
    Args:
        content: 文件内容
        filename: 文件名
    
    Returns:
        包含元数据和规则的字典
    """
    print(f"\n📋 解析文件: {filename}")
    
    lines = content.strip().split('\n')
    
    metadata = {
        'NAME': '',
        'AUTHOR': '',
        'REPO': '',
        'UPDATED': '',
        'DOMAIN-KEYWORD': 0,
        'DOMAIN-SUFFIX': 0,
        'IP-CIDR': 0,
        'IP-CIDR6': 0,
        'TOTAL': 0,
    }
    
    rules = []
    stats = {}
    skipped_rules = []
    
    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        
        # 解析注释中的元数据
        if line.startswith('#'):
            # 提取元数据
            for key in ['NAME', 'AUTHOR', 'REPO', 'UPDATED']:
                if f'# {key}:' in line:
                    metadata[key] = line.split(':', 1)[1].strip()
            
            # 提取统计信息
            for key in ['DOMAIN-KEYWORD', 'DOMAIN-SUFFIX', 'IP-CIDR', 'IP-CIDR6', 'TOTAL']:
                if f'# {key}:' in line:
                    try:
                        metadata[key] = int(line.split(':', 1)[1].strip())
                    except:
                        pass
            continue
        
        # 跳过空行
        if not line:
            continue
        
        # 解析规则
        parts = line.split(',')
        if len(parts) < 2:
            continue
        
        rule_type = parts[0].strip()
        rule_value = parts[1].strip()
        
        # 检查是否为支持的规则类型
        if rule_type in UNSUPPORTED_RULE_TYPES:
            skipped_rules.append((line_num, rule_type, rule_value))
            continue
        
        if rule_type not in SUPPORTED_RULE_TYPES:
            print(f"  ⚠️  第{line_num}行: 未知规则类型 '{rule_type}' - {line}")
            continue
        
        # 处理IP-CIDR规则（移除no-resolve等参数）
        if rule_type in ['IP-CIDR', 'IP-CIDR6']:
            # 只保留IP地址部分，去掉no-resolve等参数
            final_rule = f"{rule_type},{rule_value}"
        else:
            final_rule = f"{rule_type},{rule_value}"
        
        rules.append(final_rule)
        
        # 统计
        stats[rule_type] = stats.get(rule_type, 0) + 1
    
    # 输出解析统计
    print(f"\n  解析统计:")
    print(f"  - 总行数: {len(lines)}")
    print(f"  - 有效规则: {len(rules)}")
    
    if stats:
        print(f"\n  规则类型分布:")
        for rule_type, count in sorted(stats.items()):
            print(f"    • {rule_type}: {count}")
    
    if skipped_rules:
        print(f"\n  ⚠️  跳过的不支持规则: {len(skipped_rules)}")
        for line_num, rule_type, rule_value in skipped_rules[:5]:  # 只显示前5个
            print(f"    第{line_num}行: {rule_type},{rule_value}")
        if len(skipped_rules) > 5:
            print(f"    ... 还有 {len(skipped_rules) - 5} 个")
    
    return {
        'metadata': metadata,
        'rules': rules,
        'stats': stats
    }


def convert_to_yaml(data: Dict, original_filename: str) -> str:
    """
    转换为YAML格式
    
    Args:
        data: 解析后的数据
        original_filename: 原始文件名
    
    Returns:
        YAML格式的字符串
    """
    print(f"\n🔄 转换为YAML格式...")
    
    metadata = data['metadata']
    rules = data['rules']
    stats = data['stats']
    
    # 构建YAML内容
    yaml_lines = []
    
    # 添加注释头
    yaml_lines.append(f"# NAME: {metadata.get('NAME', '')}")
    yaml_lines.append(f"# AUTHOR: {metadata.get('AUTHOR', '')}")
    yaml_lines.append(f"# REPO: {metadata.get('REPO', '')}")
    yaml_lines.append(f"# UPDATED: {metadata.get('UPDATED', '')}")
    
    # 添加统计信息
    for key in ['DOMAIN-KEYWORD', 'DOMAIN-SUFFIX', 'IP-CIDR', 'IP-CIDR6']:
        if key in stats:
            yaml_lines.append(f"# {key}: {stats[key]}")
    
    yaml_lines.append(f"# TOTAL: {len(rules)}")
    
    # 添加payload部分
    yaml_lines.append("payload:")
    
    for rule in rules:
        yaml_lines.append(f"  - {rule}")
    
    yaml_content = '\n'.join(yaml_lines)
    
    print(f"✓ 转换完成，共 {len(rules)} 条规则")
    
    return yaml_content


def save_yaml_file(content: str, filename: str, output_dir: str = '.') -> str:
    """
    保存YAML文件
    
    Args:
        content: YAML内容
        filename: 原始文件名
        output_dir: 输出目录
    
    Returns:
        保存的文件路径
    """
    # 将.list后缀改为.yaml
    yaml_filename = filename.replace('.list', '.yaml')
    yaml_path = os.path.join(output_dir, yaml_filename)
    
    with open(yaml_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"💾 保存文件: {yaml_path}")
    
    return yaml_path


def merge_yaml_files(yaml_contents: List[Tuple[str, str]], output_dir: str = '.') -> str:
    """
    合并多个YAML文件为一个
    
    Args:
        yaml_contents: [(文件名, YAML内容), ...] 列表
        output_dir: 输出目录
    
    Returns:
        合并后的文件路径
    """
    print(f"\n🔗 合并所有YAML文件...")
    
    merged_lines = []
    
    # 添加合并文件的头部注释
    merged_lines.append("# NAME: Merged Proxy DNS Rules")
    merged_lines.append("# AUTHOR: Auto-generated")
    merged_lines.append(f"# TOTAL FILES: {len(yaml_contents)}")
    
    # 统计总规则数
    total_rules = 0
    rule_stats = {}
    
    # 收集所有规则（去重）
    all_rules = []
    seen_rules = set()
    
    for filename, content in yaml_contents:
        merged_lines.append(f"# SOURCE: {filename}")
        
        # 解析每个文件的规则
        lines = content.split('\n')
        for line in lines:
            stripped = line.strip()
            
            # 跳过注释和payload标记
            if stripped.startswith('#') or stripped == 'payload:':
                continue
            
            # 提取规则（移除前导的 "  - "）
            if stripped.startswith('- '):
                rule = stripped[2:].strip()
                
                # 去重
                if rule and rule not in seen_rules:
                    seen_rules.add(rule)
                    all_rules.append(rule)
                    
                    # 统计规则类型
                    rule_type = rule.split(',')[0]
                    rule_stats[rule_type] = rule_stats.get(rule_type, 0) + 1
                    total_rules += 1
    
    # 添加统计信息
    merged_lines.append("#")
    merged_lines.append("# Rule Statistics:")
    for rule_type, count in sorted(rule_stats.items()):
        merged_lines.append(f"# {rule_type}: {count}")
    merged_lines.append(f"# TOTAL: {total_rules}")
    merged_lines.append("#")
    
    # 添加payload部分
    merged_lines.append("payload:")
    for rule in all_rules:
        merged_lines.append(f"  - {rule}")
    
    merged_content = '\n'.join(merged_lines)
    
    # 保存合并文件
    merged_path = os.path.join(output_dir, 'need-proxy-dns.yaml')
    with open(merged_path, 'w', encoding='utf-8') as f:
        f.write(merged_content)
    
    print(f"✓ 合并完成")
    print(f"  - 源文件数: {len(yaml_contents)}")
    print(f"  - 总规则数: {total_rules} (去重后)")
    print(f"💾 保存合并文件: {merged_path}")
    
    return merged_path


def process_url(url: str, output_dir: str = '.', keep_list: bool = False) -> Tuple[bool, str, str]:
    """
    处理单个URL
    
    Args:
        url: 下载URL
        output_dir: 输出目录
        keep_list: 是否保留原始.list文件
    
    Returns:
        (是否成功, 文件名, YAML内容)
    """
    try:
        # 1. 下载文件
        content, filename = download_file(url)
        
        # 保存原始.list文件（临时）
        list_path = os.path.join(output_dir, filename)
        with open(list_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # 2. 解析文件
        data = parse_list_file(content, filename)
        
        # 3. 转换为YAML
        yaml_content = convert_to_yaml(data, filename)
        
        # 4. 保存YAML文件
        yaml_path = save_yaml_file(yaml_content, filename, output_dir)
        
        # 5. 删除原始.list文件（除非指定保留）
        if not keep_list and os.path.exists(list_path):
            os.remove(list_path)
            print(f"🗑️  删除原始文件: {list_path}")
        
        print(f"\n{'='*60}")
        print(f"✅ 成功处理: {filename} -> {os.path.basename(yaml_path)}")
        print(f"{'='*60}\n")
        
        return True, filename, yaml_content
    
    except Exception as e:
        print(f"\n❌ 处理失败: {url}")
        print(f"   错误: {e}\n")
        return False, "", ""


def main():
    """主函数"""
    # 下载URL列表的地址
    download_list_url = "https://raw.githubusercontent.com/Shinlor/ForPersonalUse/refs/heads/main/downloadurl.list"
    
    print("="*60)
    print("List to YAML 转换工具")
    print("="*60)
    print(f"\n📍 下载列表URL: {download_list_url}\n")
    
    try:
        # 下载URL列表
        list_content, _ = download_file(download_list_url)
        
        # 解析URL列表
        urls = [line.strip() for line in list_content.split('\n') 
                if line.strip() and not line.strip().startswith('#')]
        
        print(f"\n📊 找到 {len(urls)} 个下载链接\n")
        
        # 创建输出目录
        output_dir = './converted_rules'
        os.makedirs(output_dir, exist_ok=True)
        print(f"📁 输出目录: {output_dir}\n")
        
        # 处理每个URL
        success_count = 0
        fail_count = 0
        yaml_contents = []  # 存储所有成功转换的YAML内容
        
        for i, url in enumerate(urls, 1):
            print(f"\n[{i}/{len(urls)}] 处理: {url}")
            print("-"*60)
            
            success, filename, yaml_content = process_url(url, output_dir, keep_list=False)
            if success:
                success_count += 1
                yaml_contents.append((filename.replace('.list', '.yaml'), yaml_content))
            else:
                fail_count += 1
        
        # 合并所有YAML文件
        if yaml_contents:
            print("\n" + "="*60)
            merge_yaml_files(yaml_contents, output_dir)
            print("="*60)
        
        # 输出总结
        print("\n" + "="*60)
        print("转换完成总结")
        print("="*60)
        print(f"✅ 成功: {success_count}")
        print(f"❌ 失败: {fail_count}")
        print(f"📁 输出目录: {output_dir}")
        if yaml_contents:
            print(f"🔗 合并文件: {os.path.join(output_dir, 'need-proxy-dns.yaml')}")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ 程序错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
