#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
键盘重复输入延时测量工具
使用方法：
1. 运行程序
2. 长按任意一个字母键（如 'a'）
3. 程序会测量第一次重复输入的延时
4. 重复几次以获得平均值
"""

import sys
import time

def measure_keyboard_repeat():
    """测量键盘长按时的重复输入延时"""
    
    if sys.platform == 'win32':
        import msvcrt
        print("=" * 60)
        print("键盘重复输入延时测量工具 (Windows)")
        print("=" * 60)
        print("\n说明:")
        print("1. 长按任意一个字母键（如 'a', 's', 'd' 等）")
        print("2. 程序会记录第一次按键和第一次重复输入的时间")
        print("3. 按 ESC 退出")
        print("\n开始测量...\n")
        
        measurements = []
        last_key = None
        last_time = None
        
        while True:
            if msvcrt.kbhit():
                key = msvcrt.getch().decode('utf-8').lower()
                current_time = time.time()
                
                if key == '\x1b':  # ESC
                    break
                
                # 只测量字母键
                if key.isalpha():
                    if last_key == key:
                        # 同一个键的重复输入
                        delay = current_time - last_time
                        measurements.append(delay)
                        print(f"检测到重复输入 '{key}': 延时 {delay*1000:.1f} ms")
                    else:
                        # 新按键
                        print(f"新按键: '{key}'")
                    
                    last_key = key
                    last_time = current_time
    
    else:
        # Unix/Linux/Mac
        import termios
        import tty
        
        print("=" * 60)
        print("键盘重复输入延时测量工具 (Unix/Linux/Mac)")
        print("=" * 60)
        print("\n说明:")
        print("1. 长按任意一个字母键（如 'a', 's', 'd' 等）")
        print("2. 程序会记录第一次按键和第一次重复输入的时间")
        print("3. 按 ESC 退出")
        print("\n开始测量...\n")
        
        fd = sys.stdin.fileno()
        
        if not sys.stdin.isatty():
            print("错误: 这不是一个交互式终端")
            print("请在真实终端中运行此程序")
            return
        
        old_settings = termios.tcgetattr(fd)
        
        try:
            tty.setraw(sys.stdin.fileno())
            
            measurements = []
            last_key = None
            last_time = None
            
            while True:
                key = sys.stdin.read(1).lower()
                current_time = time.time()
                
                if ord(key) == 27:  # ESC
                    break
                elif ord(key) == 3:  # Ctrl+C
                    break
                
                # 只测量字母键
                if key.isalpha():
                    if last_key == key:
                        # 同一个键的重复输入
                        delay = current_time - last_time
                        measurements.append(delay)
                        print(f"检测到重复输入 '{key}': 延时 {delay*1000:.1f} ms")
                    else:
                        # 新按键
                        print(f"新按键: '{key}'")
                    
                    last_key = key
                    last_time = current_time
        
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    
    # 显示统计结果
    print("\n" + "=" * 60)
    print("测量结果")
    print("=" * 60)
    
    if len(measurements) == 0:
        print("未检测到重复输入，请长按一个键")
        return
    
    # 计算统计信息
    delays_ms = [d * 1000 for d in measurements]
    avg_delay = sum(delays_ms) / len(delays_ms)
    min_delay = min(delays_ms)
    max_delay = max(delays_ms)
    
    print(f"\n总测量次数: {len(measurements)}")
    print(f"平均延时: {avg_delay:.1f} ms")
    print(f"最小延时: {min_delay:.1f} ms")
    print(f"最大延时: {max_delay:.1f} ms")
    
    # 计算中位数
    sorted_delays = sorted(delays_ms)
    if len(sorted_delays) % 2 == 0:
        median = (sorted_delays[len(sorted_delays)//2 - 1] + sorted_delays[len(sorted_delays)//2]) / 2
    else:
        median = sorted_delays[len(sorted_delays)//2]
    print(f"中位数: {median:.1f} ms")
    
    # 推荐值（使用平均值，但至少200ms）
    recommended = max(avg_delay * 1.2, 200)  # 平均值加20%的缓冲，但至少200ms
    print(f"\n推荐阈值: {recommended:.1f} ms ({recommended/1000:.3f} 秒)")
    print("\n在 piano.py 中设置:")
    print(f"key_repeat_threshold = {recommended/1000:.3f}  # {recommended:.1f}ms")
    print("=" * 60)

if __name__ == '__main__':
    try:
        measure_keyboard_repeat()
    except KeyboardInterrupt:
        print("\n\n程序已中断")
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()







