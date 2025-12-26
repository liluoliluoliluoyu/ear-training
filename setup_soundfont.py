#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SoundFont 设置助手
帮助下载和配置 SoundFont 文件
"""

import os
import sys
import urllib.request
import shutil

def check_soundfont(path):
    """检查 SoundFont 文件是否有效"""
    if not os.path.exists(path):
        return False, "文件不存在"
    
    if os.path.getsize(path) < 1024:  # 小于1KB可能是错误文件
        return False, "文件太小，可能是错误下载"
    
    # 检查文件类型（SoundFont 文件通常以特定字节开头）
    try:
        with open(path, 'rb') as f:
            header = f.read(4)
            # SoundFont 2.0 文件通常以 "RIFF" 开头
            if header.startswith(b'RIFF') or header.startswith(b'sfbk'):
                return True, "有效的 SoundFont 文件"
            else:
                return False, "不是有效的 SoundFont 文件格式"
    except:
        return False, "无法读取文件"

def find_soundfont():
    """查找现有的 SoundFont 文件"""
    search_paths = [
        os.path.expanduser('~/soundfonts/FluidR3_GM.sf2'),
        os.path.expanduser('~/soundfonts/default.sf2'),
        'soundfonts/FluidR3_GM.sf2',
        'soundfonts/default.sf2',
        '/usr/share/sounds/sf2/FluidR3_GM.sf2',
        '/usr/share/sounds/sf2/default.sf2',
    ]
    
    for path in search_paths:
        if os.path.exists(path):
            is_valid, msg = check_soundfont(path)
            if is_valid:
                return path, True
            else:
                print(f"找到文件但无效: {path} - {msg}")
    
    return None, False

def update_piano_py(soundfont_path):
    """更新 piano.py 中的 SOUNDFONT_PATH"""
    piano_py = 'piano.py'
    if not os.path.exists(piano_py):
        print(f"错误: 找不到 {piano_py}")
        return False
    
    try:
        with open(piano_py, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 查找 SOUNDFONT_PATH 行
        lines = content.split('\n')
        updated = False
        
        for i, line in enumerate(lines):
            if line.strip().startswith('SOUNDFONT_PATH') and '=' in line:
                # 更新路径
                lines[i] = f"SOUNDFONT_PATH = r'{soundfont_path}'"
                updated = True
                break
        
        if updated:
            with open(piano_py, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines))
            print(f"✓ 已更新 {piano_py} 中的 SOUNDFONT_PATH")
            return True
        else:
            print("⚠ 未找到 SOUNDFONT_PATH 配置行，请手动设置")
            return False
    except Exception as e:
        print(f"错误: 无法更新 {piano_py}: {e}")
        return False

def main():
    print("=" * 60)
    print("SoundFont 设置助手")
    print("=" * 60)
    print()
    
    # 查找现有文件
    print("正在查找 SoundFont 文件...")
    found_path, is_valid = find_soundfont()
    
    if found_path and is_valid:
        print(f"✓ 找到有效的 SoundFont 文件: {found_path}")
        print()
        
        # 更新 piano.py
        if update_piano_py(found_path):
            print()
            print("=" * 60)
            print("设置完成！")
            print("=" * 60)
            print(f"SoundFont 路径: {found_path}")
            print("现在可以运行 piano.py 使用真实采样音色了！")
            return 0
    
    # 没有找到有效文件
    print("✗ 未找到有效的 SoundFont 文件")
    print()
    print("=" * 60)
    print("请手动下载 SoundFont 文件")
    print("=" * 60)
    print()
    print("推荐下载: FluidR3_GM.sf2 (约 140MB)")
    print()
    print("下载方式:")
    print("1. 访问: https://member.keymusician.com/Member/FluidR3_GM/")
    print("2. 或搜索: 'FluidR3_GM.sf2 download'")
    print()
    print("下载后，请将文件放在以下任一位置:")
    print(f"  - {os.path.expanduser('~/soundfonts/FluidR3_GM.sf2')}")
    print(f"  - {os.path.abspath('soundfonts/FluidR3_GM.sf2')}")
    print()
    print("然后重新运行此脚本进行设置:")
    print("  python3 setup_soundfont.py")
    print()
    
    # 创建目录
    os.makedirs(os.path.expanduser('~/soundfonts'), exist_ok=True)
    os.makedirs('soundfonts', exist_ok=True)
    print("✓ 已创建 soundfonts 目录")
    
    return 1

if __name__ == '__main__':
    sys.exit(main())







