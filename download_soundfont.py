#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""下载 SoundFont 文件"""

import os
import urllib.request
import shutil

def download_file(url, dest_path):
    """下载文件"""
    print(f"正在从 {url} 下载...")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }
    
    req = urllib.request.Request(url, headers=headers)
    
    try:
        with urllib.request.urlopen(req) as response:
            total_size = int(response.headers.get('Content-Length', 0))
            
            if total_size < 1024 * 1024:  # 小于1MB，可能是错误页面
                print(f"警告: 文件太小 ({total_size} 字节)，可能是错误页面")
                return False
            
            print(f"文件大小: {total_size / (1024*1024):.1f} MB")
            print("正在下载...")
            
            with open(dest_path, 'wb') as f:
                shutil.copyfileobj(response, f)
            
            # 验证文件
            if os.path.getsize(dest_path) > 1024 * 1024:
                # 检查文件头
                with open(dest_path, 'rb') as f:
                    header = f.read(4)
                    if header.startswith(b'RIFF') or header.startswith(b'sfbk'):
                        return True
                    else:
                        print("警告: 文件格式可能不正确")
                        return False
            return False
    except Exception as e:
        print(f"下载失败: {e}")
        return False

def main():
    print("=" * 60)
    print("SoundFont 下载工具")
    print("=" * 60)
    print()
    
    # 创建目录
    soundfont_dir = os.path.expanduser('~/soundfonts')
    os.makedirs(soundfont_dir, exist_ok=True)
    
    dest_path = os.path.join(soundfont_dir, 'FluidR3_GM.sf2')
    
    # 尝试多个下载源
    urls = [
        "https://member.keymusician.com/Member/FluidR3_GM/FluidR3_GM.sf2",
        "http://www.schristiancollins.com/soundfonts/FluidR3_GM.sf2",
    ]
    
    for url in urls:
        print(f"\n尝试源: {url}")
        if download_file(url, dest_path):
            print(f"\n✓ 下载成功！")
            print(f"文件位置: {dest_path}")
            print(f"文件大小: {os.path.getsize(dest_path) / (1024*1024):.1f} MB")
            
            # 运行设置脚本
            print("\n正在运行设置脚本...")
            import subprocess
            result = subprocess.run(['python3', 'setup_soundfont.py'], 
                                  cwd=os.path.dirname(os.path.abspath(__file__)))
            return 0
    
    print("\n✗ 所有下载源都失败了")
    print("\n请手动下载:")
    print("1. 访问: https://member.keymusician.com/Member/FluidR3_GM/")
    print("2. 下载 FluidR3_GM.sf2 文件")
    print(f"3. 将文件放在: {dest_path}")
    print("4. 运行: python3 setup_soundfont.py")
    
    return 1

if __name__ == '__main__':
    import sys
    sys.exit(main())







