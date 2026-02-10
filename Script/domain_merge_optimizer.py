#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
域名规则合并和优化工具
功能：
1. 从downloadurl.txt读取list文件的URL并下载（或使用本地文件）
2. 解析list文件中的DOMAIN和DOMAIN-SUFFIX规则
3. 合并到现有的sample.txt文件
4. 优化域名列表（去除被DOMAIN-SUFFIX包含的子域名）
"""

import sys
import os
import re
from typing import Set, List
from pathlib import Path


def download_or_load_list_file(source: str, save_dir: str = "./downloads") -> str:
    """
    下载或加载list文件
    
    参数:
        source: URL或本地文件路径
        save_dir: 保存目录（仅用于下载）
    返回:
        文件路径，失败返回None
    """
    # 判断是本地文件还是URL
    if os.path.exists(source):
        print(f"  使用本地文件: {source}")
        return source
    
    # 如果是URL，尝试下载
    if source.startswith('http://') or source.startswith('https://'):
        try:
            import requests
            
            # 创建下载目录
            os.makedirs(save_dir, exist_ok=True)
            
            # 从URL中提取文件名
            filename = source.split('/')[-1]
            if '?' in filename:
                filename = filename.split('?')[0]
            if not filename.endswith('.list'):
                filename = filename + '.list'
            
            filepath = os.path.join(save_dir, filename)
            
            # 下载文件
            print(f"  正在下载: {source}")
            response = requests.get(source, timeout=30)
            response.raise_for_status()
            
            # 保存文件
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            print(f"  ✓ 已保存到: {filepath}")
            return filepath
        
        except ImportError:
            print(f"  ✗ 需要安装requests库: pip install requests")
            return None
        except Exception as e:
            print(f"  ✗ 下载失败: {e}")
            return None
    else:
        print(f"  ✗ 无效的源: {source}")
        return None


def parse_list_file(filepath: str) -> tuple:
    """
    解析list文件，提取DOMAIN和DOMAIN-SUFFIX规则
    
    参数:
        filepath: list文件路径
    返回:
        (domains集合, domain_suffixes集合)
    """
    domains = set()
    domain_suffixes = set()
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                
                # 跳过注释和空行
                if not line or line.startswith('#'):
                    continue
                
                # 解析DOMAIN规则
                if line.startswith('DOMAIN,'):
                    domain = line.split(',', 1)[1].strip()
                    if domain:
                        domains.add(domain)
                
                # 解析DOMAIN-SUFFIX规则
                elif line.startswith('DOMAIN-SUFFIX,'):
                    suffix = line.split(',', 1)[1].strip()
                    if suffix:
                        domain_suffixes.add(suffix)
        
        print(f"    解析: {len(domains)} 个DOMAIN, {len(domain_suffixes)} 个DOMAIN-SUFFIX")
    
    except Exception as e:
        print(f"    ✗ 解析失败: {e}")
    
    return domains, domain_suffixes


def is_subdomain_of(domain: str, suffix: str) -> bool:
    """
    判断domain是否是suffix的子域名
    
    参数:
        domain: 要检查的域名
        suffix: 后缀域名
    返回:
        True表示是子域名
    """
    # 如果完全相同，不算子域名
    if domain == suffix:
        return False
    
    # 检查是否以.suffix结尾
    if domain.endswith('.' + suffix):
        return True
    
    return False


def optimize_domains(all_domains: Set[str], domain_suffixes: Set[str]) -> Set[str]:
    """
    优化域名列表，移除被DOMAIN-SUFFIX包含的子域名
    
    参数:
        all_domains: 所有域名集合
        domain_suffixes: DOMAIN-SUFFIX集合
    返回:
        优化后的域名集合
    """
    optimized = set()
    removed_count = 0
    
    for domain in all_domains:
        # 检查是否被任何suffix包含
        is_covered = False
        for suffix in domain_suffixes:
            if is_subdomain_of(domain, suffix):
                is_covered = True
                removed_count += 1
                break
        
        if not is_covered:
            optimized.add(domain)
    
    if removed_count > 0:
        print(f"  优化: 移除了 {removed_count} 个被DOMAIN-SUFFIX覆盖的子域名")
    
    return optimized


def load_existing_domains(filepath: str) -> Set[str]:
    """
    加载现有的sample.txt文件中的域名
    
    参数:
        filepath: sample.txt文件路径
    返回:
        域名集合
    """
    domains = set()
    
    if not os.path.exists(filepath):
        print(f"  文件不存在: {filepath}，将创建新文件")
        return domains
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    domains.add(line)
        
        print(f"  已加载: {len(domains)} 个域名")
    
    except Exception as e:
        print(f"  ✗ 加载失败: {e}")
    
    return domains


def save_domains(domains: Set[str], filepath: str):
    """
    保存域名到文件（排序后）
    
    参数:
        domains: 域名集合
        filepath: 输出文件路径
    """
    try:
        # 排序（不区分大小写）
        sorted_domains = sorted(domains, key=lambda x: x.lower())
        
        with open(filepath, 'w', encoding='utf-8') as f:
            for domain in sorted_domains:
                f.write(domain + '\n')
        
        print(f"  ✓ 已保存 {len(sorted_domains)} 个域名到: {filepath}")
    
    except Exception as e:
        print(f"  ✗ 保存失败: {e}")


def main():
    """主函数"""
    print("=" * 60)
    print("域名规则合并和优化工具")
    print("=" * 60)
    print()
    
    # 文件路径
    download_urls_file = "downloadurl.txt"
    domain_list_dir = "./DomainList"  # 域名列表目录
    sample_file = os.path.join(domain_list_dir, "proxy-list.txt")
    output_file = os.path.join(domain_list_dir, "proxy-list.txt")
    downloaded_url_file = None  # 记录是否下载了downloadurl文件
    
    # 确保DomainList目录存在
    os.makedirs(domain_list_dir, exist_ok=True)
    
    # 允许用户自定义文件路径
    if len(sys.argv) >= 2:
        download_urls_file = sys.argv[1]
    if len(sys.argv) >= 3:
        sample_file = sys.argv[2]
    if len(sys.argv) >= 4:
        output_file = sys.argv[3]
    
    # 检查downloadurl.txt是否存在，如果不存在则从GitHub下载
    if not os.path.exists(download_urls_file):
        default_url = "https://raw.githubusercontent.com/Shinlor/ForPersonalUse/refs/heads/main/Script/downloadurl.list"
        print(f"⚠ 未找到文件 {download_urls_file}")
        print(f"  将从默认地址下载: {default_url}")
        downloaded_file = download_or_load_list_file(default_url, save_dir=".")
        if downloaded_file:
            download_urls_file = downloaded_file
            downloaded_url_file = downloaded_file  # 记录下载的文件路径
            print(f"  ✓ 已下载并使用: {download_urls_file}\n")
        else:
            print(f"✗ 错误: 下载失败且本地文件不存在")
            print(f"请手动创建 {download_urls_file} 文件，或检查网络连接")
            sys.exit(1)
    
    # 读取源列表（URL或本地文件路径）
    print(f"步骤 1: 读取源列表")
    print(f"  文件: {download_urls_file}")
    sources = []
    with open(download_urls_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                sources.append(line)
    
    print(f"  找到 {len(sources)} 个源\n")
    
    if len(sources) == 0:
        print("✗ 错误: 没有找到任何源")
        sys.exit(1)
    
    # 下载或加载list文件
    print(f"步骤 2: 加载list文件")
    loaded_files = []
    for source in sources:
        filepath = download_or_load_list_file(source)
        if filepath:
            loaded_files.append(filepath)
    
    print(f"  成功加载: {len(loaded_files)}/{len(sources)} 个文件\n")
    
    if len(loaded_files) == 0:
        print("✗ 错误: 没有成功加载任何文件")
        sys.exit(1)
    
    # 解析list文件
    print(f"步骤 3: 解析list文件")
    all_domains = set()
    all_suffixes = set()
    
    for filepath in loaded_files:
        print(f"  文件: {os.path.basename(filepath)}")
        domains, suffixes = parse_list_file(filepath)
        all_domains.update(domains)
        all_suffixes.update(suffixes)
    
    print(f"  总计: {len(all_domains)} 个DOMAIN, {len(all_suffixes)} 个DOMAIN-SUFFIX\n")
    
    # 加载现有的proxy-list.txt
    print(f"步骤 4: 加载现有域名")
    print(f"  文件: {sample_file}")
    
    existing_domains = load_existing_domains(sample_file)
    print()
    
    # 合并所有域名
    print(f"步骤 5: 合并域名")
    original_count = len(all_domains)
    all_domains.update(existing_domains)
    all_domains.update(all_suffixes)  # DOMAIN-SUFFIX也加入域名列表
    print(f"  合并后: {len(all_domains)} 个域名\n")
    
    # 优化域名列表
    print(f"步骤 6: 优化域名列表")
    optimized_domains = optimize_domains(all_domains, all_suffixes)
    print(f"  优化后: {len(optimized_domains)} 个域名\n")
    
    # 保存结果
    print(f"步骤 7: 保存结果")
    save_domains(optimized_domains, output_file)
    
    print()
    print("=" * 60)
    print("处理完成！")
    print("=" * 60)
    print(f"统计信息:")
    print(f"  原有域名数量:        {len(existing_domains)}")
    print(f"  新增DOMAIN规则:      {len(all_domains - existing_domains - all_suffixes)}")
    print(f"  新增DOMAIN-SUFFIX:   {len(all_suffixes)}")
    print(f"  去重后总数:          {len(all_domains)}")
    print(f"  优化后输出:          {len(optimized_domains)}")
    print(f"  输出文件:            {output_file}")
    print("=" * 60)
    
    # 清理下载的临时文件
    if downloaded_url_file and os.path.exists(downloaded_url_file):
        try:
            os.remove(downloaded_url_file)
            print(f"\n✓ 已清理临时文件: {downloaded_url_file}")
        except Exception as e:
            print(f"\n⚠ 清理临时文件失败: {e}")
    
    # 新增：清理 downloads 目录
    downloads_dir = "./downloads"
    if os.path.exists(downloads_dir):
        try:
            import shutil
            shutil.rmtree(downloads_dir)
            print(f"✓ 已删除目录: {downloads_dir}")
        except Exception as e:
            print(f"⚠ 删除目录失败: {e}")




if __name__ == "__main__":
    main()
