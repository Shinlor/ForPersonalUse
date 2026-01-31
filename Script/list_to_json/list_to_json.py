#!/usr/bin/env python3
"""
从URL下载list文件并转换为json文件的脚本
"""
import json
import sys
import os
import requests
from urllib.parse import urlparse


def download_file(url, output_path):
    """
    从URL下载文件
    
    参数:
        url: 文件下载地址
        output_path: 保存文件的路径
    
    返回:
        bool: 下载是否成功
    """
    try:
        print(f"正在下载: {url}")
        response = requests.get(url, timeout=30)
        response.raise_for_status()  # 检查HTTP错误
        
        with open(output_path, 'wb') as f:
            f.write(response.content)
        
        print(f"下载成功: {output_path}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"下载失败: {e}")
        return False


def check_list_file(file_path):
    """
    检查list文件是否有效
    
    参数:
        file_path: list文件路径
    
    返回:
        bool: 文件是否有效
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        if not lines:
            print("警告: 文件为空")
            return False
        
        valid_types = ['DOMAIN', 'DOMAIN-KEYWORD', 'DOMAIN-SUFFIX', 
                       'IP-CIDR', 'IP-CIDR6', 'USER-AGENT', 'PROCESS-NAME']
        
        valid_count = 0
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            parts = line.split(',')
            if len(parts) >= 2 and parts[0].upper() in valid_types:
                valid_count += 1
        
        print(f"文件检查通过: 共 {len(lines)} 行, {valid_count} 条有效规则")
        return True
    except Exception as e:
        print(f"文件检查失败: {e}")
        return False


def list_to_json(list_file_path, json_file_path, version=2):
    """
    将list文件转换为json格式
    
    参数:
        list_file_path: 输入的list文件路径
        json_file_path: 输出的json文件路径
        version: json文件的版本号,默认为2
    
    返回:
        bool: 转换是否成功
    """
    # 初始化结果字典
    result = {
        "rules": [
            {"domain": []},
            {"domain_keyword": []},
            {"domain_suffix": []}
        ],
        "version": version
    }
    
    # 读取list文件
    try:
        with open(list_file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"错误: 找不到文件 {list_file_path}")
        return False
    
    # 统计信息
    stats = {
        'domain': 0,
        'domain_keyword': 0,
        'domain_suffix': 0,
        'ignored': 0
    }
    
    # 处理每一行
    for line in lines:
        line = line.strip()
        if not line:  # 跳过空行
            continue
        
        # 分割行内容
        parts = line.split(',')
        if len(parts) < 2:
            continue
        
        rule_type = parts[0].upper()
        value = parts[1]
        
        # 根据规则类型分类
        if rule_type == 'DOMAIN':
            result["rules"][0]["domain"].append(value)
            stats['domain'] += 1
        elif rule_type == 'DOMAIN-KEYWORD':
            result["rules"][1]["domain_keyword"].append(value)
            stats['domain_keyword'] += 1
        elif rule_type == 'DOMAIN-SUFFIX':
            result["rules"][2]["domain_suffix"].append(value)
            stats['domain_suffix'] += 1
        else:
            # 其他类型(IP-CIDR, IP-CIDR6, USER-AGENT, PROCESS-NAME等)将被忽略
            stats['ignored'] += 1
    
    # 写入json文件
    try:
        with open(json_file_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"\n转换统计:")
        print(f"  - DOMAIN: {stats['domain']} 条")
        print(f"  - DOMAIN-KEYWORD: {stats['domain_keyword']} 条")
        print(f"  - DOMAIN-SUFFIX: {stats['domain_suffix']} 条")
        print(f"  - 已忽略: {stats['ignored']} 条")
        print(f"\n成功: 已生成 {json_file_path}")
        return True
    except Exception as e:
        print(f"错误: 写入文件时出错 - {e}")
        return False


def get_filename_from_url(url):
    """
    从URL中提取文件名
    
    参数:
        url: 文件URL
    
    返回:
        str: 文件名
    """
    parsed_url = urlparse(url)
    path = parsed_url.path
    filename = os.path.basename(path)
    
    # 如果URL没有文件名，使用默认名称
    if not filename or '.' not in filename:
        filename = 'downloaded.list'
    
    return filename


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python list_to_json.py <list文件URL> [版本号] [输出目录]")
        print("示例: python list_to_json.py https://example.com/rules.list 2 ./output")
        print("\n说明:")
        print("  - list文件URL: 必需，list文件的下载地址")
        print("  - 版本号: 可选，json文件的version值，默认为2")
        print("  - 输出目录: 可选，输出文件的目录，默认为当前目录")
        sys.exit(1)
    
    url = sys.argv[1]
    version = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    output_dir = sys.argv[3] if len(sys.argv) > 3 else '.'
    
    # 确保输出目录存在
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"已创建输出目录: {output_dir}")
    
    # 从URL获取文件名
    list_filename = get_filename_from_url(url)
    list_filepath = os.path.join(output_dir, list_filename)
    
    # 生成json文件名（替换扩展名）
    json_filename = os.path.splitext(list_filename)[0] + '.json'
    json_filepath = os.path.join(output_dir, json_filename)
    
    print(f"输出目录: {output_dir}")
    print(f"List文件: {list_filename}")
    print(f"JSON文件: {json_filename}")
    print("-" * 50)
    
    # 下载文件
    if not download_file(url, list_filepath):
        sys.exit(1)
    
    # 检查文件
    print("-" * 50)
    if not check_list_file(list_filepath):
        print("警告: 文件检查未通过，但将继续转换")
    
    # 转换为json
    print("-" * 50)
    if list_to_json(list_filepath, json_filepath, version):
        print("-" * 50)
        print(f"✓ 完成! JSON文件已保存到: {json_filepath}")
    else:
        print("-" * 50)
        print("✗ 转换失败")
        sys.exit(1)


if __name__ == "__main__":
    main()
