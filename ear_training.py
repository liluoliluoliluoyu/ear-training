#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
练耳程序 - 听音识谱训练
播放6个音符的组合，用户输入答案进行练习
"""

import sys
import random
import time
import os

# 导入钢琴程序的播放功能
try:
    # 尝试导入piano.py中的功能
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from piano import start_note, stop_note, init_audio, init_soundfont, cleanup_audio, FLUIDSYNTH_AVAILABLE
    from piano import SAMPLE_RATE, KEY_MAP, INSTRUMENTS
except ImportError:
    print("错误: 无法导入 piano.py 的功能")
    sys.exit(1)

# 白键音符（不带升降号）- 使用piano.py的按键映射
# 按键 -> 音符名称映射（只使用白键）
KEY_TO_NOTE = {
    'a': 'C',  # C4
    's': 'D',  # D4
    'd': 'E',  # E4
    'f': 'F',  # F4
    'g': 'G',  # G4
    'h': 'A',  # A4
    'j': 'B',  # B4
    'k': 'C5',  # C5 (高音C)
}

# 音符名称到频率的映射
NOTE_TO_FREQ = {
    'C': 261.63,   # C4
    'D': 293.66,   # D4
    'E': 329.63,   # E4
    'F': 349.23,   # F4
    'G': 392.00,   # G4
    'A': 440.00,   # A4
    'B': 493.88,   # B4
    'C5': 523.25,  # C5 (高音C)
}

# 音符名称列表（用于显示和输入）
NOTE_NAMES = ['C', 'D', 'E', 'F', 'G', 'A', 'B']

def play_reference_note(duration=1.0):
    """播放基准音C（延长播放以便区分）"""
    if 'C' in NOTE_TO_FREQ:
        frequency = NOTE_TO_FREQ['C']
        key_id = f"ref_C_{time.time()}"
        start_note(key_id, frequency, '1')  # 使用钢琴音色
        time.sleep(duration)  # 延长播放时间
        stop_note(key_id)
        time.sleep(0.5)  # 基准音后明显停顿，与题目音符区分

def play_note_sequence(notes, duration=0.5, pause=0.1, play_reference=True):
    """播放一系列音符（支持C5高音，可选择是否播放基准音）"""
    # 播放基准音C
    if play_reference:
        play_reference_note(duration=0.6)
    
    for i, note in enumerate(notes):
        # 处理C5高音
        note_key = note if note in NOTE_TO_FREQ else note
        if note_key in NOTE_TO_FREQ:
            frequency = NOTE_TO_FREQ[note_key]
            key_id = f"ear_{note}_{i}_{time.time()}"
            start_note(key_id, frequency, '1')  # 使用钢琴音色
            time.sleep(duration)
            stop_note(key_id)
            if i < len(notes) - 1:  # 最后一个音符后不需要暂停
                time.sleep(pause)

def generate_sequence(length=6):
    """生成随机音符序列（可以包含高音C）"""
    # 音符池：包含普通音符和高音C
    note_pool = NOTE_NAMES + ['C5']
    return [random.choice(note_pool) for _ in range(length)]

def format_answer(notes):
    """格式化答案（去除空格，转为大写，支持C5）"""
    if not notes:
        return ''
    
    # 如果notes是列表，先转换为字符串
    if isinstance(notes, list):
        notes = ''.join(notes)
    
    result = []
    i = 0
    notes_upper = notes.upper()
    while i < len(notes_upper):
        # 检查是否是C5（优先检查，因为C5是两字符）
        if i < len(notes_upper) - 1 and notes_upper[i:i+2] == 'C5':
            result.append('C5')
            i += 2
        elif notes_upper[i] in NOTE_NAMES:
            result.append(notes_upper[i])
            i += 1
        else:
            # 跳过无效字符
            i += 1
    return ''.join(result)

def get_user_input(allow_replay=False, sequence=None):
    """获取用户输入（使用piano.py的按键映射，支持试音和重放）"""
    if sys.platform == 'win32':
        import msvcrt
        print("\n操作说明:")
        print("  • 使用按键试音: A S D F G H J K (对应 C D E F G A B C5)")
        print("  • 按回车确认答案")
        if allow_replay:
            print("  • 按 R 重放题目")
        print("  • 按ESC退出")
        print("\n输入答案: ", end='', flush=True)
        answer = []
        while True:
            if msvcrt.kbhit():
                key = msvcrt.getch().decode('utf-8').lower()
                if key == '\r' or key == '\n':  # 回车
                    if answer:  # 有答案才确认
                        break
                elif key == '\x08' or ord(key) == 127:  # 退格
                    if answer:
                        answer.pop()
                        print('\b \b', end='', flush=True)
                elif key == 'r' and allow_replay and sequence:  # 重放
                    print("\n\n🎵 重放基准音C...")
                    time.sleep(0.1)
                    print("🎵 重放中...")
                    play_note_sequence(sequence, duration=0.6, pause=0.15, play_reference=True)
                    print("✓ 播放完成！")
                    print("\n输入答案: ", end='', flush=True)
                    # 重新显示已输入的内容
                    for char in answer:
                        print(char, end='', flush=True)
                elif key in KEY_TO_NOTE:
                    # 使用piano.py的按键映射
                    note = KEY_TO_NOTE[key]
                    answer.append(note)
                    print(note, end='', flush=True)
                    # 播放对应音符
                    if note in NOTE_TO_FREQ:
                        note_key = f"input_{note}_{time.time()}"
                        start_note(note_key, NOTE_TO_FREQ[note], '1')
                        time.sleep(0.3)
                        stop_note(note_key)
                elif key == '\x1b':  # ESC
                    return None
        print()  # 换行
        return ''.join(answer)
    else:
        # Unix/Linux/Mac
        import termios
        import tty
        
        fd = sys.stdin.fileno()
        if not sys.stdin.isatty():
            print("错误: 这不是交互式终端")
            return None
        
        old_settings = termios.tcgetattr(fd)
        
        try:
            tty.setraw(sys.stdin.fileno())
            print("\n操作说明:")
            print("  • 使用按键试音: A S D F G H J K (对应 C D E F G A B C5)")
            print("  • 按回车确认答案")
            if allow_replay:
                print("  • 按 R 重放题目")
            print("  • 按ESC退出")
            print("\n输入答案: ", end='', flush=True)
            answer = []
            while True:
                key = sys.stdin.read(1).lower()
                if key == '\r' or key == '\n':  # 回车
                    if answer:  # 有答案才确认
                        break
                elif ord(key) == 127 or ord(key) == 8:  # 退格
                    if answer:
                        answer.pop()
                        print('\b \b', end='', flush=True)
                elif key == 'r' and allow_replay and sequence:  # 重放
                    print("\n\n🎵 重放基准音C...")
                    time.sleep(0.1)
                    print("🎵 重放中...")
                    play_note_sequence(sequence, duration=0.6, pause=0.15, play_reference=True)
                    print("✓ 播放完成！")
                    print("\n输入答案: ", end='', flush=True)
                    # 重新显示已输入的内容
                    for char in answer:
                        print(char, end='', flush=True)
                elif key in KEY_TO_NOTE:
                    # 使用piano.py的按键映射
                    note = KEY_TO_NOTE[key]
                    answer.append(note)
                    print(note, end='', flush=True)
                    # 播放对应音符
                    if note in NOTE_TO_FREQ:
                        note_key = f"input_{note}_{time.time()}"
                        start_note(note_key, NOTE_TO_FREQ[note], '1')
                        time.sleep(0.3)
                        stop_note(note_key)
                elif ord(key) == 27:  # ESC
                    return None
            print()  # 换行
            return ''.join(answer)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

def main():
    """主程序"""
    print("=" * 60)
    print("练耳程序 - 听音识谱训练")
    print("=" * 60)
    print("\n📝 说明:")
    print("  • 程序会播放6个音符的组合")
    print("  • 使用按键试音: A S D F G H J K (对应 C D E F G A B C5)")
    print("  • 可以不断试音，程序会自动取最后6个音符作为答案")
    print("  • 按 R 可以重放题目")
    print("  • 按回车确认答案")
    print("  • 按ESC退出程序")
    print("\n🎵 音符: C D E F G A B C5（白键，包含高音C）")
    print("=" * 60)
    
    # 初始化音频
    if not init_audio():
        print("错误: 无法初始化音频设备")
        return
    
    # 尝试初始化 SoundFont
    if FLUIDSYNTH_AVAILABLE:
        init_soundfont()
    
    print("\n准备开始...")
    time.sleep(1)
    
    correct_count = 0
    total_count = 0
    
    try:
        while True:
            total_count += 1
            
            # 生成新的音符序列
            sequence = generate_sequence(6)
            # correct_answer用于显示，保持原始格式
            correct_answer = ''.join(sequence)
            
            print(f"\n{'='*60}")
            print(f"第 {total_count} 题")
            print(f"{'='*60}")
            print("\n🎵 正在播放基准音C...")
            time.sleep(0.2)
            print("🎵 正在播放音符序列...")
            time.sleep(0.1)
            
            # 播放音符序列（包含基准音）
            play_note_sequence(sequence, duration=0.6, pause=0.15, play_reference=True)
            
            print("✓ 播放完成！")
            time.sleep(0.2)
            
            # 获取用户输入（允许重放）
            user_answer = get_user_input(allow_replay=True, sequence=sequence)
            
            if user_answer is None:  # ESC退出
                print("\n退出程序")
                break
            
            # 检查答案（取最后6个音符进行比较）
            user_answer_formatted = format_answer(user_answer)
            user_answer_clean = user_answer_formatted[-6:] if len(user_answer_formatted) > 6 else user_answer_formatted  # 取最后6个
            correct_answer_clean = format_answer(correct_answer)
            
            if user_answer_clean == correct_answer_clean:
                correct_count += 1
                accuracy = (correct_count / total_count) * 100
                print(f"\n{'='*60}")
                print(f"🎉 正确！")
                print(f"正确答案: {correct_answer}")
                print(f"📊 当前正确率: {correct_count}/{total_count} ({accuracy:.1f}%)")
                print(f"{'='*60}")
                time.sleep(0.5)
            else:
                accuracy = (correct_count / total_count) * 100
                print(f"\n{'='*60}")
                print(f"❌ 错误")
                print(f"你的答案（最后6个）: {user_answer_clean if user_answer_clean else '(空)'}")
                print(f"完整输入: {user_answer if user_answer else '(空)'}")
                print(f"正确答案: {correct_answer}")
                print(f"📊 当前正确率: {correct_count}/{total_count} ({accuracy:.1f}%)")
                print(f"{'='*60}")
                print("\n🔄 再试一次...")
                time.sleep(0.5)
                
                # 重新播放
                print("\n🎵 重新播放...")
                play_note_sequence(sequence, duration=0.6, pause=0.15)
                print("✓ 播放完成！")
                time.sleep(0.2)
                
                # 再次获取输入（允许重放）
                user_answer = get_user_input(allow_replay=True, sequence=sequence)
                if user_answer is None:
                    break
                
                user_answer_formatted = format_answer(user_answer)
                user_answer_clean = user_answer_formatted[-6:] if len(user_answer_formatted) > 6 else user_answer_formatted  # 取最后6个
                if user_answer_clean == correct_answer_clean:
                    correct_count += 1
                    accuracy = (correct_count / total_count) * 100
                    print(f"\n{'='*60}")
                    print(f"🎉 正确！")
                    print(f"正确答案: {correct_answer}")
                    print(f"📊 当前正确率: {correct_count}/{total_count} ({accuracy:.1f}%)")
                    print(f"{'='*60}")
                    time.sleep(0.5)
                else:
                    print(f"\n{'='*60}")
                    print(f"❌ 仍然错误")
                    print(f"正确答案: {correct_answer}")
                    print(f"{'='*60}")
                    time.sleep(0.8)
    
    except KeyboardInterrupt:
        print("\n\n程序已中断")
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cleanup_audio()
        
        # 显示最终统计
        if total_count > 0:
            print("\n" + "=" * 60)
            print("练习结束")
            print("=" * 60)
            print(f"总题数: {total_count}")
            print(f"正确数: {correct_count}")
            print(f"正确率: {(correct_count / total_count) * 100:.1f}%")
            print("=" * 60)

if __name__ == '__main__':
    main()

