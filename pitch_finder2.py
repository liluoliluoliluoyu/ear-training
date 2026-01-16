#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
音高寻找练耳程序 v2 - 自动切换音阶版本
自动播放下一个音，可调整音符持续时间和间隔
"""

import sys
import random
import time
import os
import threading
import math

# 导入钢琴程序的播放功能
try:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from piano import start_note, stop_note, init_audio, init_soundfont, cleanup_audio, FLUIDSYNTH_AVAILABLE
    from piano import SAMPLE_RATE, KEY_MAP, INSTRUMENTS
except ImportError as e:
    print(f"错误: 无法导入 piano.py 的功能")
    print(f"详细错误: {e}")
    sys.exit(1)
except SystemExit:
    print("\n请确保已安装所有依赖:")
    print("pip install pyaudio numpy pyFluidSynth")
    sys.exit(1)

# 频率容差（Hz）
FREQUENCY_TOLERANCE = 1.0

# 全局状态
current_scale = None
current_scale_id = None  # 当前音阶的唯一ID
is_playing = False
is_paused = False
scale_thread = None
found_count = 0
total_attempts = 0
start_time = None

# 可调参数
note_duration = 1.5  # 音符持续时间（秒）
note_interval = 0.3  # 音符间隔（秒）
scale_interval = 1.0  # 音阶之间的间隔（秒）

# 锁
state_lock = threading.Lock()

def frequency_to_note_name(frequency):
    """将频率转换为音符名称"""
    note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    midi_note = 12 * (math.log2(frequency / 440.0)) + 69
    midi_note = round(midi_note)
    octave = (midi_note - 12) // 12
    note_index = midi_note % 12
    note_name = note_names[note_index]
    
    if 520 <= frequency <= 530:
        return "C5"
    elif 261 <= frequency <= 263:
        return "C4"
    elif 440 <= frequency <= 442:
        return "A4"
    
    return f"{note_name}{octave}"

def are_frequencies_match(freq1, freq2, tolerance=FREQUENCY_TOLERANCE):
    """判断两个频率是否匹配"""
    return abs(freq1 - freq2) <= tolerance

def generate_scale():
    """生成新的音阶（仅使用C4到C5的白键）"""
    global current_scale
    white_keys_c4_c5 = ['a', 's', 'd', 'f', 'g', 'h', 'j', 'k']
    white_key_frequencies = [KEY_MAP[key] for key in white_keys_c4_c5]
    current_scale = [random.choice(white_key_frequencies)]
    return current_scale

def play_scale_loop():
    """循环播放音阶（自动切换）"""
    global current_scale, current_scale_id, is_playing, is_paused, note_duration, note_interval, scale_interval
    
    while is_playing:
        if is_paused:
            time.sleep(0.1)
            continue
        
        # 生成新音阶并设置新的ID
        with state_lock:
            generate_scale()
            current_scale_id = time.time()  # 使用时间戳作为唯一ID
            scale_copy = current_scale.copy()
            duration = note_duration
            interval = note_interval
            scale_gap = scale_interval
        
        # 播放当前音阶
        for i, freq in enumerate(scale_copy):
            if not is_playing:
                break
            
            while is_paused and is_playing:
                time.sleep(0.1)
            
            if not is_playing:
                break
            
            # 播放音符
            note_key = f"scale_{i}_{time.time()}"
            start_note(note_key, freq, '1')
            time.sleep(duration)
            stop_note(note_key)
            
            # 音符之间的间隔
            if i < len(scale_copy) - 1:
                time.sleep(interval)
        
        # 音阶之间的间隔（自动切换）
        if is_playing:
            time.sleep(scale_gap)

def get_user_input(fd=None, raw_mode=False):
    """获取用户按键输入（非阻塞）"""
    if sys.platform == 'win32':
        import msvcrt
        if msvcrt.kbhit():
            try:
                key = msvcrt.getch().decode('utf-8').lower()
                return key
            except:
                return None
    else:
        import select
        if not sys.stdin.isatty():
            return None
        
        if raw_mode and fd is not None:
            if select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], []):
                try:
                    key = sys.stdin.read(1).lower()
                    return key
                except:
                    return None
    return None

def main():
    """主程序"""
    global current_scale, current_scale_id, is_playing, is_paused, scale_thread
    global found_count, total_attempts, start_time
    global note_duration, note_interval, scale_interval
    
    print("=" * 60)
    print("音高寻找练耳程序 v2 - 自动切换音阶")
    print("=" * 60)
    print("\n📝 说明:")
    print("  • 程序会自动播放并切换音阶")
    print("  • 按键盘按键试音，找到匹配的音高")
    print("\n⌨️  按键操作:")
    print("  • 音符键: A S D F G H J K (试音)")
    print("  • 空格键: 暂停/继续")
    print("  • [ / ]: 调整音符持续时间")
    print("  • , / .: 调整音符间隔")
    print("  • ESC: 退出")
    print("=" * 60)
    
    # 初始化音频
    if not init_audio():
        print("错误: 无法初始化音频设备")
        return
    
    if FLUIDSYNTH_AVAILABLE:
        init_soundfont()
    
    print("\n准备开始...")
    time.sleep(0.5)
    
    # 生成第一个音阶
    current_scale = generate_scale()
    current_scale_id = time.time()  # 初始化音阶ID
    is_playing = True
    start_time = time.time()
    
    # 启动音阶播放线程
    scale_thread = threading.Thread(target=play_scale_loop, daemon=True)
    scale_thread.start()
    
    # 用户按键跟踪
    pressed_keys = {}
    user_note_keys = {}
    current_scale_id = None  # 当前音阶ID
    attempted_scale_id = None  # 已经尝试过的音阶ID
    
    print("\n🎵 音阶已开始播放（自动切换）")
    print(f"当前设置: 持续时间={note_duration:.1f}s, 间隔={note_interval:.1f}s\n")
    
    # 设置终端为raw模式
    original_settings = None
    fd = None
    if sys.platform != 'win32':
        import termios
        import tty
        if sys.stdin.isatty():
            fd = sys.stdin.fileno()
            original_settings = termios.tcgetattr(fd)
            tty.setraw(fd)
    
    try:
        while True:
            key = get_user_input(fd=fd, raw_mode=True)
            
            if key is None:
                time.sleep(0.01)
                continue
            
            # ESC退出
            try:
                if ord(key) == 27:
                    print("\n\n退出程序...")
                    break
            except:
                pass
            
            # 空格键：暂停/继续
            if key == ' ':
                is_paused = not is_paused
                status = "暂停" if is_paused else "继续"
                print(f"\r⏸️  {status}", end='', flush=True)
                continue
            
            # [ / ]: 调整音符持续时间
            if key == '[':
                note_duration = max(0.3, note_duration - 0.1)
                print(f"\r持续时间: {note_duration:.1f}s", end='', flush=True)
                continue
            if key == ']':
                note_duration = min(3.0, note_duration + 0.1)
                print(f"\r持续时间: {note_duration:.1f}s", end='', flush=True)
                continue
            
            # , / .: 调整音符间隔
            if key == ',':
                note_interval = max(0.0, note_interval - 0.1)
                print(f"\r间隔: {note_interval:.1f}s", end='', flush=True)
                continue
            if key == '.':
                note_interval = min(2.0, note_interval + 0.1)
                print(f"\r间隔: {note_interval:.1f}s", end='', flush=True)
                continue
            
            # 处理音符按键
            if key in KEY_MAP:
                user_freq = KEY_MAP[key]
                
                # 如果按键已经在播放，停止并重新开始
                if key in user_note_keys:
                    stop_note(user_note_keys[key])
                    del user_note_keys[key]
                    if key in pressed_keys:
                        del pressed_keys[key]
                
                # 播放用户按键的音符
                user_note_key = f"user_{key}_{time.time()}"
                start_note(user_note_key, user_freq, '2')
                user_note_keys[key] = user_note_key
                pressed_keys[key] = time.time()
                
                # 检查是否匹配（只统计第一次按键）
                match_found = False
                should_count = False  # 是否应该统计这次尝试
                
                # 获取当前音阶ID
                with state_lock:
                    scale_id = current_scale_id
                    scale_copy = current_scale.copy() if current_scale else None
                
                # 如果是新的音阶（还没有尝试过），才统计
                if scale_id is not None and scale_id != attempted_scale_id:
                    should_count = True
                    attempted_scale_id = scale_id
                    total_attempts += 1
                
                # 检查是否匹配
                if scale_copy:
                    for scale_freq in scale_copy:
                        if are_frequencies_match(user_freq, scale_freq):
                            match_found = True
                            break
                
                # 只有第一次按键才统计匹配
                if should_count and match_found:
                    found_count += 1
                
                # 简化输出
                user_note = frequency_to_note_name(user_freq)
                if should_count:
                    # 第一次按键，显示统计信息
                    accuracy = (found_count / total_attempts * 100) if total_attempts > 0 else 0
                    if match_found:
                        print(f"\r✓ {user_note} | 匹配率: {found_count}/{total_attempts} ({accuracy:.0f}%)", end='', flush=True)
                    else:
                        print(f"\r{user_note} | {found_count}/{total_attempts} ({accuracy:.0f}%)", end='', flush=True)
                else:
                    # 后续按键，只显示音符，不更新统计
                    if match_found:
                        print(f"\r✓ {user_note}", end='', flush=True)
                    else:
                        print(f"\r{user_note}", end='', flush=True)
            
            # 检查按键释放
            current_time = time.time()
            keys_to_release = []
            for k, press_time in pressed_keys.items():
                if current_time - press_time > 1.0:
                    keys_to_release.append(k)
            
            for k in keys_to_release:
                if k in user_note_keys:
                    stop_note(user_note_keys[k])
                    del user_note_keys[k]
                del pressed_keys[k]
    
    except KeyboardInterrupt:
        print("\n\n程序已中断")
    except Exception as e:
        print(f"\n错误: {e}")
    finally:
        # 恢复终端设置
        if sys.platform != 'win32' and original_settings is not None and fd is not None:
            try:
                import termios
                termios.tcsetattr(fd, termios.TCSADRAIN, original_settings)
            except:
                pass
        
        is_playing = False
        
        for note_key in user_note_keys.values():
            stop_note(note_key)
        
        if scale_thread and scale_thread.is_alive():
            scale_thread.join(timeout=1.0)
        
        cleanup_audio()
        
        # 显示统计信息
        elapsed_time = time.time() - start_time if start_time else 0
        print("\n" + "=" * 60)
        print("练习结束")
        print("=" * 60)
        print(f"总尝试: {total_attempts} | 匹配: {found_count}", end='')
        if total_attempts > 0:
            print(f" | 匹配率: {(found_count / total_attempts * 100):.1f}%")
        else:
            print()
        print(f"时长: {elapsed_time:.0f}秒")
        print("=" * 60)

if __name__ == '__main__':
    import math
    main()

