#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
音高寻找练耳程序 - 持续播放音阶，通过按键寻找匹配的音高
播放音阶的同时，用户可以通过按键试音，找到匹配的音高
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
    print("\n请确保:")
    print("1. 已安装依赖: pip install pyaudio numpy")
    print("2. 如果使用虚拟环境，请先激活: source venv/bin/activate")
    sys.exit(1)
except SystemExit:
    # piano.py 在导入时可能因为依赖问题退出
    print("\n请确保已安装所有依赖:")
    print("pip install pyaudio numpy pyFluidSynth")
    print("\n如果使用虚拟环境，请先激活:")
    print("source venv/bin/activate")
    sys.exit(1)

# 频率容差（Hz）- 用于判断两个音是否匹配
FREQUENCY_TOLERANCE = 1.0

# 全局状态
current_scale = None  # 当前播放的音阶
current_scale_index = 0  # 当前播放到音阶的第几个音符
is_playing = False  # 是否正在播放
is_paused = False  # 是否暂停
playback_speed = 1.0  # 播放速度（倍数）
scale_thread = None  # 音阶播放线程
found_count = 0  # 找到匹配音的次数
total_attempts = 0  # 总尝试次数
start_time = None  # 开始时间

# 锁
state_lock = threading.Lock()

def frequency_to_note_name(frequency):
    """将频率转换为音符名称（近似）"""
    # 标准音高：A4 = 440Hz
    note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    
    # 计算最接近的MIDI音符
    midi_note = 12 * (math.log2(frequency / 440.0)) + 69
    
    # 四舍五入到最近的整数
    midi_note = round(midi_note)
    
    # 计算八度和音符名称
    octave = (midi_note - 12) // 12
    note_index = midi_note % 12
    
    note_name = note_names[note_index]
    
    # 特殊处理：如果频率接近C5，显示为C5
    if 520 <= frequency <= 530:
        return "C5"
    elif 261 <= frequency <= 263:
        return "C4"
    elif 440 <= frequency <= 442:
        return "A4"
    
    return f"{note_name}{octave}"

def are_frequencies_match(freq1, freq2, tolerance=FREQUENCY_TOLERANCE):
    """判断两个频率是否匹配（在容差范围内）"""
    return abs(freq1 - freq2) <= tolerance

def generate_scale(scale_type='single', length=1):
    """生成音阶（仅使用C4到C5的白键）"""
    global current_scale
    
    # C4到C5的白键：C4, D4, E4, F4, G4, A4, B4, C5
    white_keys_c4_c5 = ['a', 's', 'd', 'f', 'g', 'h', 'j', 'k']
    white_key_frequencies = [KEY_MAP[key] for key in white_keys_c4_c5]
    
    if scale_type == 'single':
        # 单音模式：随机选择一个白键音符
        current_scale = [random.choice(white_key_frequencies)]
    elif scale_type == 'sequence':
        # 序列模式：随机选择多个白键音符
        current_scale = random.sample(white_key_frequencies, min(length, len(white_key_frequencies)))
    else:
        # 默认：单音
        current_scale = [random.choice(white_key_frequencies)]
    
    return current_scale

def play_scale_loop():
    """循环播放音阶（在独立线程中运行）"""
    global current_scale, current_scale_index, is_playing, is_paused
    
    while is_playing:
        if is_paused:
            time.sleep(0.1)
            continue
        
        if current_scale:
            with state_lock:
                scale_copy = current_scale.copy()
                speed = playback_speed
            
            for i, freq in enumerate(scale_copy):
                if not is_playing:
                    break
                
                while is_paused and is_playing:
                    time.sleep(0.1)
                
                if not is_playing:
                    break
                
                # 播放当前音符（使用不同的key_id以便区分）
                note_key = f"scale_{i}_{time.time()}"
                start_note(note_key, freq, '1')  # 使用钢琴音色
                
                # 根据播放速度调整持续时间（延长到1.5秒）
                duration = 1.5 / speed
                time.sleep(duration)
                
                stop_note(note_key)
                
                # 音符之间的间隔
                if i < len(scale_copy) - 1:
                    time.sleep(0.15 / speed)
        
        # 音阶之间的间隔
        if is_playing:
            time.sleep(0.3 / speed)

def get_key_name(frequency):
    """根据频率找到对应的按键名称"""
    for key, freq in KEY_MAP.items():
        if are_frequencies_match(freq, frequency):
            return key
    return None

def format_frequency(freq):
    """格式化频率显示"""
    return f"{freq:.2f} Hz"

def get_user_input(fd=None, raw_mode=False):
    """获取用户按键输入（非阻塞，不需要按回车）"""
    if sys.platform == 'win32':
        import msvcrt
        if msvcrt.kbhit():
            try:
                key = msvcrt.getch().decode('utf-8').lower()
                return key
            except:
                return None
    else:
        # Unix/Linux/Mac - 使用select实现非阻塞输入
        import select
        
        if not sys.stdin.isatty():
            return None
        
        # 如果已经在raw模式，直接读取
        if raw_mode and fd is not None:
            if select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], []):
                try:
                    key = sys.stdin.read(1).lower()
                    return key
                except:
                    return None
        else:
            # 临时设置raw模式读取
            import termios
            import tty
            
            if select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], []):
                if fd is None:
                    fd = sys.stdin.fileno()
                old_settings = termios.tcgetattr(fd)
                try:
                    tty.setraw(sys.stdin.fileno())
                    key = sys.stdin.read(1).lower()
                    return key
                except:
                    return None
                finally:
                    termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return None

def main():
    """主程序"""
    global current_scale, is_playing, is_paused, scale_thread
    global found_count, total_attempts, start_time, playback_speed
    
    print("=" * 70)
    print("音高寻找练耳程序 - 持续播放音阶，通过按键寻找匹配的音高")
    print("=" * 70)
    print("\n📝 说明:")
    print("  • 程序会持续播放音阶（循环播放）")
    print("  • 使用按键试音，找到与播放音阶匹配的音高")
    print("  • 当找到匹配音时，会听到两个音同时播放，并显示提示")
    print("  • 按键映射参考 piano.py")
    print("\n⌨️  按键操作:")
    print("  • 音符键: A S D F G H J K (C4到C5的白键)")
    print("  • 空格键: 暂停/继续播放")
    print("  • N 键: 生成新的音阶")
    print("  • +/- 键: 调整播放速度")
    print("  • ESC: 退出程序")
    print("\n🎵 音符范围: C4 到 C5（仅白键：C D E F G A B C5）")
    print("=" * 70)
    
    # 初始化音频
    if not init_audio():
        print("错误: 无法初始化音频设备")
        return
    
    # 尝试初始化 SoundFont
    if FLUIDSYNTH_AVAILABLE:
        init_soundfont()
    
    print("\n准备开始...")
    time.sleep(1)
    
    # 生成第一个音阶
    current_scale = generate_scale('single', 1)
    is_playing = True
    start_time = time.time()
    
    # 启动音阶播放线程
    scale_thread = threading.Thread(target=play_scale_loop, daemon=True)
    scale_thread.start()
    
    # 用户按键跟踪
    pressed_keys = {}  # {key: press_time}
    user_note_keys = {}  # {key: note_key_id} 用于跟踪用户按下的音符
    
    print(f"\n{'='*70}")
    print("🎵 音阶已开始播放！")
    scale_names = [frequency_to_note_name(f) for f in current_scale]
    print(f"当前音阶: {', '.join(scale_names)} ({', '.join([format_frequency(f) for f in current_scale])})")
    print(f"播放速度: {playback_speed:.1f}x")
    print(f"{'='*70}")
    print("\n💡 提示: 按键盘按键试音，找到匹配的音高！")
    print("   • 音阶使用钢琴音色（持续循环播放）")
    print("   • 你的按键使用吉他音色（便于区分）")
    print("   • 找到匹配音时，会听到两个音同时播放，并显示 ✓ 提示")
    print("   • 可以长按按键来持续试音\n")
    
    # 设置终端为raw模式（Unix系统），这样不需要按回车
    original_settings = None
    fd = None
    if sys.platform != 'win32':
        import termios
        import tty
        if sys.stdin.isatty():
            fd = sys.stdin.fileno()
            original_settings = termios.tcgetattr(fd)
            tty.setraw(fd)  # 设置为raw模式，不需要按回车
    
    try:
        while True:
            key = get_user_input(fd=fd, raw_mode=True)
            
            if key is None:
                time.sleep(0.01)  # 避免CPU占用过高
                continue
            
            # ESC退出
            try:
                if ord(key) == 27:  # ESC
                    print("\n\n退出程序...")
                    break
            except:
                pass
            
            # 空格键：暂停/继续
            if key == ' ':
                is_paused = not is_paused
                status = "暂停" if is_paused else "继续"
                print(f"\n⏸️  播放已{status}")
                continue
            
            # N键：生成新音阶（支持不同模式）
            if key == 'n':
                # 随机选择音阶类型
                scale_types = ['single', 'sequence']
                scale_type = random.choice(scale_types)
                length = random.randint(1, 3) if scale_type == 'sequence' else 1
                current_scale = generate_scale(scale_type, length)
                scale_info = [frequency_to_note_name(f) for f in current_scale]
                print(f"\n🔄 生成新音阶: {', '.join(scale_info)} ({[format_frequency(f) for f in current_scale]})")
                continue
            
            # +/- 键：调整播放速度
            if key == '+' or key == '=':
                playback_speed = min(playback_speed + 0.1, 3.0)
                print(f"\n⚡ 播放速度: {playback_speed:.1f}x")
                continue
            if key == '-' or key == '_':
                playback_speed = max(playback_speed - 0.1, 0.3)
                print(f"\n⚡ 播放速度: {playback_speed:.1f}x")
                continue
            
            # 处理音符按键
            if key in KEY_MAP:
                user_freq = KEY_MAP[key]
                total_attempts += 1
                
                # 如果按键已经在播放，停止并重新开始（允许重新触发）
                if key in user_note_keys:
                    stop_note(user_note_keys[key])
                    del user_note_keys[key]
                    if key in pressed_keys:
                        del pressed_keys[key]
                
                # 开始播放用户按下的音符（使用不同的音色以便区分）
                # 使用不同的乐器（如吉他）来区分用户按键和音阶播放
                user_note_key = f"user_{key}_{time.time()}"
                start_note(user_note_key, user_freq, '2')  # 使用吉他音色以便区分
                user_note_keys[key] = user_note_key
                pressed_keys[key] = time.time()
                
                # 检查是否匹配当前播放的音阶
                match_found = False
                matched_freq = None
                
                if current_scale:
                    for scale_freq in current_scale:
                        if are_frequencies_match(user_freq, scale_freq):
                            match_found = True
                            matched_freq = scale_freq
                            break
                
                # 显示信息
                user_note = frequency_to_note_name(user_freq)
                scale_info = [frequency_to_note_name(f) for f in current_scale] if current_scale else []
                
                if match_found:
                    found_count += 1
                    accuracy = (found_count / total_attempts * 100) if total_attempts > 0 else 0
                    print(f"\n{'='*70}")
                    print(f"🎉 ✓ 找到匹配音！")
                    print(f"   你的按键: {key.upper()} → {user_note} ({format_frequency(user_freq)})")
                    print(f"   匹配音阶: {frequency_to_note_name(matched_freq)} ({format_frequency(matched_freq)})")
                    print(f"   当前音阶: {', '.join(scale_info)}")
                    print(f"   📊 匹配率: {found_count}/{total_attempts} ({accuracy:.1f}%)")
                    print(f"{'='*70}")
                else:
                    accuracy = (found_count / total_attempts * 100) if total_attempts > 0 else 0
                    # 计算与当前音阶的差距
                    if current_scale:
                        min_diff = min([abs(user_freq - f) for f in current_scale])
                        direction = "↑" if user_freq > current_scale[0] else "↓"
                        print(f"   按键: {key.upper()} → {user_note} ({format_frequency(user_freq)}) | "
                              f"音阶: {', '.join(scale_info)} | "
                              f"差距: {min_diff:.1f} Hz {direction} | "
                              f"匹配率: {found_count}/{total_attempts} ({accuracy:.1f}%)", end='\r')
            
            # 检查按键释放（长按支持：按键后1秒自动释放，或用户再次按下同一键）
            current_time = time.time()
            keys_to_release = []
            for k, press_time in pressed_keys.items():
                # 如果按键超过1秒，自动释放（允许长按但不要太长）
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
        import traceback
        traceback.print_exc()
    finally:
        # 恢复终端设置（Unix系统）
        if sys.platform != 'win32' and original_settings is not None and fd is not None:
            try:
                import termios
                termios.tcsetattr(fd, termios.TCSADRAIN, original_settings)
            except:
                pass
        # 停止播放
        is_playing = False
        
        # 停止所有用户按键的音符
        for note_key in user_note_keys.values():
            stop_note(note_key)
        
        # 等待线程结束
        if scale_thread and scale_thread.is_alive():
            scale_thread.join(timeout=1.0)
        
        cleanup_audio()
        
        # 显示统计信息
        elapsed_time = time.time() - start_time if start_time else 0
        print("\n" + "=" * 70)
        print("练习结束")
        print("=" * 70)
        print(f"总尝试次数: {total_attempts}")
        print(f"找到匹配次数: {found_count}")
        if total_attempts > 0:
            print(f"匹配率: {(found_count / total_attempts * 100):.1f}%")
        print(f"练习时长: {elapsed_time:.1f} 秒")
        print("=" * 70)

if __name__ == '__main__':
    import math
    main()

