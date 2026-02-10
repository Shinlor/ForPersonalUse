#!/usr/bin/env python3
"""
List to JSON Converter (Merged Version)
将.list文件转换为.json格式的脚本（合并版本）
支持批量下载、转换、合并功能
"""

import json
import os
import sys
import requests
from pathlib import Path
from urllib.parse import urlparse


# 默认的downloadurl.list下载地址
DEFAULT_DOWNLOADURL = "https://raw.githubusercontent.com/Shinlor/ForPersonalUse/refs/heads/main/downloadurl.list"

# 输出目录
OUTPUT_DIR = "./Rules/Sing-Box"


def download_file(url, local_path):
    """下载文件到本地"""
    try:
        print(f"正在下载: {url}")
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        with open(local_path, 'wb') as f:
            f.write(response.content)
        print(f"下载成功: {local_path}")
        return True
    except Exception as e:
        print(f"下载失败 {url}: {e}")
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
            if not line or line.startswith('#'):
                continue
            
            parts = line.split(',')
            if len(parts) >= 2 and parts[0].upper() in valid_types:
                valid_count += 1
        
        print(f"文件检查通过: 共 {len(lines)} 行, {valid_count} 条有效规则")
        return True
    except Exception as e:
        print(f"文件检查失败: {e}")
        return False


def parse_list_file(list_file_path):
    """解析.list文件并转换为JSON结构（支持IP-CIDR）"""
    rules_data = {
        "domain": [],
        "domain_keyword": [],
        "domain_suffix": [],
        "ip_cidr": []
    }
    
    with open(list_file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            
            # 跳过注释和空行
            if not line or line.startswith('#'):
                continue
            
            # 解析不同类型的规则
            if line.startswith('DOMAIN,'):
                domain = line.split(',', 1)[1]
                rules_data["domain"].append(domain)
                
            elif line.startswith('DOMAIN-KEYWORD,'):
                keyword = line.split(',', 1)[1]
                rules_data["domain_keyword"].append(keyword)
                
            elif line.startswith('DOMAIN-SUFFIX,'):
                suffix = line.split(',', 1)[1]
                rules_data["domain_suffix"].append(suffix)
                
            elif line.startswith('IP-CIDR,') or line.startswith('IP-CIDR6,'):
                # 提取IP-CIDR，去除no-resolve等后缀
                parts = line.split(',')
                ip_cidr = parts[1]
                rules_data["ip_cidr"].append(ip_cidr)
    
    # 构建最终的JSON结构
    final_rules = []
    
    # 添加domain规则（如果有）
    if rules_data["domain"]:
        final_rules.append({"domain": rules_data["domain"]})
    
    # 添加domain_keyword规则（如果有）
    if rules_data["domain_keyword"]:
        final_rules.append({"domain_keyword": rules_data["domain_keyword"]})
    
    # 添加domain_suffix规则（如果有）
    if rules_data["domain_suffix"]:
        final_rules.append({"domain_suffix": rules_data["domain_suffix"]})
    
    # 添加ip_cidr规则（如果有）
    if rules_data["ip_cidr"]:
        final_rules.append({"ip_cidr": rules_data["ip_cidr"]})
    
    return {
        "rules": final_rules,
        "version": 2
    }


def convert_list_to_json(list_file_path, json_file_path, version=2):
    """
    将单个.list文件转换为.json文件
    
    参数:
        list_file_path: 输入的list文件路径
        json_file_path: 输出的json文件路径
        version: json文件的版本号,默认为2
    
    返回:
        bool: 转换是否成功
    """
    try:
        # 解析list文件
        json_data = parse_list_file(list_file_path)
        
        # 统计信息
        stats = {
            'domain': 0,
            'domain_keyword': 0,
            'domain_suffix': 0,
            'ip_cidr': 0
        }
        
        for rule in json_data["rules"]:
            if "domain" in rule:
                stats['domain'] = len(rule["domain"])
            if "domain_keyword" in rule:
                stats['domain_keyword'] = len(rule["domain_keyword"])
            if "domain_suffix" in rule:
                stats['domain_suffix'] = len(rule["domain_suffix"])
            if "ip_cidr" in rule:
                stats['ip_cidr'] = len(rule["ip_cidr"])
        
        # 写入JSON文件
        with open(json_file_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n转换统计:")
        print(f"  - DOMAIN: {stats['domain']} 条")
        print(f"  - DOMAIN-KEYWORD: {stats['domain_keyword']} 条")
        print(f"  - DOMAIN-SUFFIX: {stats['domain_suffix']} 条")
        print(f"  - IP-CIDR: {stats['ip_cidr']} 条")
        print(f"✓ 转换成功: {list_file_path} -> {json_file_path}")
        return True
    except Exception as e:
        print(f"✗ 转换失败 {list_file_path}: {e}")
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


def merge_json_files(json_files, output_path, version=2):
    """
    合并多个json文件
    
    参数:
        json_files: json文件路径列表
        output_path: 合并后的输出文件路径
        version: json文件的版本号
    
    返回:
        bool: 合并是否成功
    """
    merged_result = {
        "rules": [],
        "version": version
    }
    
    # 初始化合并数据结构（包含IP-CIDR）
    merged_data = {
        "domain": [],
        "domain_keyword": [],
        "domain_suffix": [],
        "ip_cidr": []
    }
    
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # 合并各个规则类型（包含IP-CIDR）
            if "rules" in data:
                for rule in data["rules"]:
                    if "domain" in rule:
                        merged_data["domain"].extend(rule["domain"])
                    if "domain_keyword" in rule:
                        merged_data["domain_keyword"].extend(rule["domain_keyword"])
                    if "domain_suffix" in rule:
                        merged_data["domain_suffix"].extend(rule["domain_suffix"])
                    if "ip_cidr" in rule:
                        merged_data["ip_cidr"].extend(rule["ip_cidr"])
        except Exception as e:
            print(f"警告: 读取 {json_file} 失败 - {e}")
            continue
    
    # 去重
    merged_data["domain"] = list(set(merged_data["domain"]))
    merged_data["domain_keyword"] = list(set(merged_data["domain_keyword"]))
    merged_data["domain_suffix"] = list(set(merged_data["domain_suffix"]))
    merged_data["ip_cidr"] = list(set(merged_data["ip_cidr"]))
    
    # 构建最终的JSON结构（包含所有规则类型）
    if merged_data["domain"]:
        merged_result["rules"].append({"domain": merged_data["domain"]})
    if merged_data["domain_keyword"]:
        merged_result["rules"].append({"domain_keyword": merged_data["domain_keyword"]})
    if merged_data["domain_suffix"]:
        merged_result["rules"].append({"domain_suffix": merged_data["domain_suffix"]})
    if merged_data["ip_cidr"]:
        merged_result["rules"].append({"ip_cidr": merged_data["ip_cidr"]})
    
    # 写入合并后的文件
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(merged_result, f, indent=2, ensure_ascii=False)
        
        total_domain = len(merged_data["domain"])
        total_keyword = len(merged_data["domain_keyword"])
        total_suffix = len(merged_data["domain_suffix"])
        total_ip = len(merged_data["ip_cidr"])
        
        print(f"\n合并统计:")
        print(f"  - DOMAIN: {total_domain} 条")
        print(f"  - DOMAIN-KEYWORD: {total_keyword} 条")
        print(f"  - DOMAIN-SUFFIX: {total_suffix} 条")
        print(f"  - IP-CIDR: {total_ip} 条")
        print(f"  - 总计: {total_domain + total_keyword + total_suffix + total_ip} 条")
        print(f"\n成功: 已生成合并文件 {output_path}")
        return True
    except Exception as e:
        print(f"错误: 写入合并文件时出错 - {e}")
        return False


def cleanup_temp_files(temp_files, temp_dir=None):
    """
    清理临时文件和临时目录
    
    参数:
        temp_files: 需要删除的临时文件列表
        temp_dir: 临时目录路径（可选），如果提供则在清理文件后删除该目录
    """
    print("\n" + "=" * 50)
    print("开始清理临时文件")
    print("=" * 50)
    
    deleted_count = 0
    for temp_file in temp_files:
        try:
            if os.path.exists(temp_file):
                os.remove(temp_file)
                print(f"✓ 已删除: {temp_file}")
                deleted_count += 1
        except Exception as e:
            print(f"✗ 删除失败 {temp_file}: {e}")
    
    print(f"\n清理完成: 共删除 {deleted_count} 个临时文件")
    
    # 如果提供了临时目录路径，尝试删除该目录
    if temp_dir:
        try:
            if os.path.exists(temp_dir):
                os.rmdir(temp_dir)
                print(f"✓ 已删除临时目录: {temp_dir}")
        except Exception as e:
            print(f"✗ 删除临时目录失败 {temp_dir}: {e}")


def batch_process(downloadurl_file, output_dir=OUTPUT_DIR, version=2):
    """
    批量处理downloadurl文件中的所有URL
    
    参数:
        downloadurl_file: URL列表文件路径
        output_dir: 输出目录
        version: json文件的版本号
    
    返回:
        bool: 处理是否成功
    """
    # 读取URL列表
    try:
        with open(downloadurl_file, 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        print(f"从 {downloadurl_file} 读取到 {len(urls)} 个URL")
    except Exception as e:
        print(f"读取URL文件失败: {e}")
        return False
    
    if not urls:
        print("URL列表为空")
        return False
    
    # 确保输出目录存在
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    print(f"输出目录: {output_dir}")
    
    # 创建临时目录存放下载的文件
    temp_dir = Path(output_dir) / "temp_downloads"
    temp_dir.mkdir(exist_ok=True)
    
    print("\n" + "=" * 50)
    print(f"开始批量处理 {len(urls)} 个URL")
    print("=" * 50)
    
    json_files = []
    list_files = []  # 跟踪下载的list文件
    success_count = 0
    fail_count = 0
    
    # 处理每个URL
    for idx, url in enumerate(urls, 1):
        # 从URL中提取文件名
        filename = get_filename_from_url(url)
        
        # 只处理.list文件
        if not filename.endswith('.list'):
            print(f"[{idx}/{len(urls)}] 跳过非.list文件: {filename}")
            continue
        
        print(f"\n[{idx}/{len(urls)}] 处理: {filename}")
        print("-" * 50)
        
        # 下载.list文件到临时目录
        list_file_path = temp_dir / filename
        if not download_file(url, list_file_path):
            fail_count += 1
            continue
        
        list_files.append(str(list_file_path))  # 记录下载的list文件
        
        # 检查文件
        if not check_list_file(list_file_path):
            print("警告: 文件检查未通过，但将继续转换")
        
        # 生成JSON文件名，直接保存到输出目录（不再使用序号前缀）
        json_filename = filename.replace('.list', '.json')
        json_file_path = Path(output_dir) / json_filename
        
        # 转换为JSON
        if convert_list_to_json(list_file_path, json_file_path, version):
            json_files.append(str(json_file_path))
            success_count += 1
        else:
            fail_count += 1
    
    # 输出单独文件的统计信息
    print("\n" + "=" * 50)
    print(f"单文件转换完成")
    print(f"成功: {success_count} 个文件")
    print(f"失败: {fail_count} 个文件")
    print("=" * 50)
    
    # 合并所有json文件
    if json_files:
        print("\n" + "=" * 50)
        print(f"开始合并 {len(json_files)} 个JSON文件")
        print("=" * 50)
        
        merged_filepath = Path(output_dir) / 'NeedProxydns.json'
        if merge_json_files(json_files, merged_filepath, version):
            # 清理临时下载的list文件和临时目录，保留生成的JSON文件
            cleanup_temp_files(list_files, temp_dir)
            
            print("\n" + "=" * 50)
            print(f"✓ 批量处理完成!")
            print(f"  - 成功: {success_count}/{len(urls)}")
            print(f"  - 单独JSON文件: {len(json_files)} 个（已保留在输出目录）")
            print(f"  - 合并文件: {merged_filepath}")
            print("=" * 50)
            return True
    else:
        print("\n" + "=" * 50)
        print("✗ 没有成功转换的文件，无法生成合并文件")
        print("=" * 50)
        
        # 即使失败也清理已下载的文件和临时目录
        if list_files:
            cleanup_temp_files(list_files, temp_dir)
        else:
            # 如果没有文件也尝试删除临时目录
            try:
                if os.path.exists(temp_dir):
                    os.rmdir(temp_dir)
                    print(f"✓ 已删除临时目录: {temp_dir}")
            except:
                pass
        
        return False


def main():
    """主函数"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    downloadurl_file = os.path.join(script_dir, 'downloadurl.list')
    url_file_downloaded = False  # 标记文件是否是自动下载的
    
    # 检查是否存在downloadurl.list文件
    if not os.path.exists(downloadurl_file):
        print("未检测到 downloadurl.list 文件")
        print(f"正在从默认地址下载: {DEFAULT_DOWNLOADURL}")
        if download_file(DEFAULT_DOWNLOADURL, downloadurl_file):
            url_file_downloaded = True
            print("✓ downloadurl.list 下载成功\n")
        else:
            print("✗ 下载 downloadurl.list 失败")
            sys.exit(1)
    else:
        print("检测到 downloadurl.list 文件")
    
    # 获取参数
    version = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    output_dir = sys.argv[2] if len(sys.argv) > 2 else OUTPUT_DIR
    
    print(f"启动批量处理模式")
    print(f"版本号: {version}")
    print(f"输出目录: {output_dir}\n")
    
    # 批量处理
    result = batch_process(downloadurl_file, output_dir, version)
    
    # 如果downloadurl.list是自动下载的，处理完成后删除它
    if url_file_downloaded and os.path.exists(downloadurl_file):
        try:
            os.remove(downloadurl_file)
            print(f"\n✓ 已删除自动下载的 downloadurl.list")
        except Exception as e:
            print(f"\n✗ 删除 downloadurl.list 失败: {e}")
    
    if result:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
