#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
音高寻找练耳程序 v3 - 批量播放版本
播放一批随机音符，可重复多次，然后切换到下一批
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

# ============================================================================
# 参数配置区域 - 统一在此处修改
# ============================================================================
# t1: 单个音符的持续时间（秒）
T1_NOTE_DURATION = 0.6

# t2: 同一批里不同音符之间的间隔时间（秒）
T2_NOTE_INTERVAL = 0.2

# t3: 同一批重复播放两次之间的间隔时间（秒）
T3_REPEAT_INTERVAL = 2

# t4: 不同批之间的间隔时间（秒）
T4_BATCH_INTERVAL = 2

# n1: 一批音符的数量
N1_NOTES_PER_BATCH = 6

# n2: 一批重复播放的次数
N2_REPEAT_COUNT = 100

# 频率容差（Hz）
FREQUENCY_TOLERANCE = 1.0
# ============================================================================

# 全局状态
current_batch = None  # 当前一批音符
current_scale_id = None  # 当前批次的唯一ID
is_playing = False
is_paused = False
scale_thread = None
start_time = None
skip_remaining_repeats = False  # 是否跳过当前批次的剩余重复

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

def generate_batch():
    """生成新的一批音符（n1个随机音符，仅使用C4到C5的白键）"""
    global current_batch
    white_keys_c4_c5 = ['a', 's', 'd', 'f', 'g', 'h', 'j', 'k']
    white_key_frequencies = [KEY_MAP[key] for key in white_keys_c4_c5]
    # 生成 n1 个随机音符（允许重复）
    current_batch = [random.choice(white_key_frequencies) for _ in range(N1_NOTES_PER_BATCH)]
    return current_batch

def play_batch_loop():
    """循环播放批次（自动切换）"""
    global current_batch, current_scale_id, is_playing, is_paused, skip_remaining_repeats
    
    while is_playing:
        if is_paused:
            time.sleep(0.1)
            continue
        
        # 生成新批次并设置新的ID
        with state_lock:
            generate_batch()
            current_scale_id = time.time()  # 使用时间戳作为唯一ID
            batch_copy = current_batch.copy()
            skip_remaining_repeats = False  # 重置跳过标志
            t1 = T1_NOTE_DURATION
            t2 = T2_NOTE_INTERVAL
            t3 = T3_REPEAT_INTERVAL
            t4 = T4_BATCH_INTERVAL
            n2 = N2_REPEAT_COUNT
        
        # 重复播放 n2 次
        for repeat in range(n2):
            if not is_playing:
                break
            
            # 检查是否要跳过剩余重复
            if skip_remaining_repeats:
                break
            
            # 播放当前批次的所有音符
            for i, freq in enumerate(batch_copy):
                if not is_playing:
                    break
                
                # 再次检查是否要跳过（可能在播放过程中被设置）
                if skip_remaining_repeats:
                    break
                
                while is_paused and is_playing:
                    time.sleep(0.1)
                
                if not is_playing:
                    break
                
                # 播放音符
                note_key = f"batch_{repeat}_{i}_{time.time()}"
                start_note(note_key, freq, '1')
                time.sleep(t1)  # t1: 单个音符的持续时间
                stop_note(note_key)
                
                # t2: 同一批里不同音符之间的间隔时间
                if i < len(batch_copy) - 1:
                    time.sleep(t2)
            
            # t3: 同一批重复播放两次之间的间隔时间（如果不是最后一次重复，且未跳过）
            if repeat < n2 - 1 and is_playing and not skip_remaining_repeats:
                time.sleep(t3)
        
        # t4: 不同批之间的间隔时间（自动切换到下一批）
        if is_playing:
            time.sleep(t4)

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
    global current_batch, current_scale_id, is_playing, is_paused, scale_thread
    global start_time, skip_remaining_repeats
    
    print("=" * 60)
    print("音高寻找练耳程序 v3 - 批量播放版本")
    print("=" * 60)
    print("\n📝 说明:")
    print(f"  • 程序会自动播放一批 {N1_NOTES_PER_BATCH} 个随机音符")
    print(f"  • 每批重复播放 {N2_REPEAT_COUNT} 次，然后切换到下一批")
    print("  • 按键盘按键试音，找到匹配的音高")
    print("\n⌨️  按键操作:")
    print("  • 音符键: A S D F G H J K (试音)")
    print("  • 空格键: 暂停/继续")
    print("  • N 键: 跳过当前批次剩余重复，进入下一批")
    print("  • ESC: 退出")
    print("\n⚙️  当前参数:")
    print(f"  • 音符持续时间 (t1): {T1_NOTE_DURATION:.1f}s")
    print(f"  • 音符间隔 (t2): {T2_NOTE_INTERVAL:.1f}s")
    print(f"  • 重复间隔 (t3): {T3_REPEAT_INTERVAL:.1f}s")
    print(f"  • 批次间隔 (t4): {T4_BATCH_INTERVAL:.1f}s")
    print(f"  • 每批音符数 (n1): {N1_NOTES_PER_BATCH}")
    print(f"  • 重复次数 (n2): {N2_REPEAT_COUNT}")
    print("=" * 60)
    
    # 初始化音频
    if not init_audio():
        print("错误: 无法初始化音频设备")
        return
    
    if FLUIDSYNTH_AVAILABLE:
        init_soundfont()
    
    print("\n准备开始...")
    time.sleep(0.5)
    
    # 生成第一个批次
    current_batch = generate_batch()
    current_scale_id = time.time()  # 初始化批次ID
    is_playing = True
    start_time = time.time()
    
    # 启动批次播放线程
    scale_thread = threading.Thread(target=play_batch_loop, daemon=True)
    scale_thread.start()
    
    # 用户按键跟踪
    pressed_keys = {}
    user_note_keys = {}
    
    print("\n🎵 批次已开始播放（自动切换）\n")
    
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
            
            # N 键：跳过当前批次剩余重复
            if key == 'n':
                with state_lock:
                    skip_remaining_repeats = True
                print(f"\r⏭️  跳过剩余重复，进入下一批", end='', flush=True)
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
                
                # 检查是否匹配
                match_found = False
                
                # 获取当前批次
                with state_lock:
                    batch_copy = current_batch.copy() if current_batch else None
                
                # 检查是否匹配（检查批次中的任何一个音符）
                if batch_copy:
                    for batch_freq in batch_copy:
                        if are_frequencies_match(user_freq, batch_freq):
                            match_found = True
                            break
                
                # 输出
                user_note = frequency_to_note_name(user_freq)
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
        
        # 显示结束信息
        elapsed_time = time.time() - start_time if start_time else 0
        print("\n" + "=" * 60)
        print("练习结束")
        print("=" * 60)
        print(f"时长: {elapsed_time:.0f}秒")
        print("=" * 60)

if __name__ == '__main__':
    import math
    main()
