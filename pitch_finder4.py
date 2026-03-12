#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
音高寻找练耳程序 v4 - QWERTY 自然音阶 + 变调
键位：q～i 低八度八个音(do～do)，o p 不发音，a～k 中高八度(a=中音do k=高音do)，l 不发音，z x c v b=高音 do re mi fa sol，n 下一批。
支持 +/- 整体升降八度、Shift 临时升八度。
"""

import sys
import random
import time
import os
import threading
import math

try:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from piano import start_note, stop_note, init_audio, init_soundfont, cleanup_audio, FLUIDSYNTH_AVAILABLE
    from piano import SAMPLE_RATE, INSTRUMENTS
except ImportError as e:
    print(f"错误: 无法导入 piano.py 的功能")
    print(f"详细错误: {e}")
    sys.exit(1)
except SystemExit:
    print("\n请确保已安装所有依赖:")
    print("pip install pyaudio numpy pyFluidSynth")
    sys.exit(1)

# ============================================================================
# 常量配置
# ============================================================================
# 键盘：q～i 低八度八个音(do～do)，o p 不发音，a～k 中高八度(a=中音do k=高音do)，l 不发音，z x c v b=高音 do re mi fa sol
KEY_ORDER = list('qwertyuiopasdfghjklzxcvb')
# 低八度八个音（C3～C4），对应 q w e r t y u i
LOW_OCTAVE_HZ = (130.81, 146.83, 164.81, 174.61, 196.00, 220.00, 246.94, 261.63)  # C3 D3 E3 F3 G3 A3 B3 C4
# 中高八度八个音（C4～C5），对应 a s d f g h j k
MIDDLE_OCTAVE_HZ = (261.63, 293.66, 329.63, 349.23, 392.00, 440.00, 493.88, 523.25)  # C4 D4 E4 F4 G4 A4 B4 C5
# 不发音的键
SILENT_KEYS = ('o', 'p', 'l')
# 高音 do re mi fa sol（C5～G5），对应 z x c v b
HIGH_DO_RE_MI_FA_SOL_HZ = (523.25, 587.33, 659.25, 698.46, 783.99)

# 中音 do 频率（C4），供 note_name_to_freq、出题范围等使用
MIDDLE_DO_HZ = 261.63
# 自然大调各音相对 do 的半音数（出题用）
DIATONIC_SEMITONES = [0, 2, 4, 5, 7, 9, 11]  # C D E F G A B

# 测试音范围（音名，只在此范围内出题；可改为如 "G3"、"D5"）
TEST_NOTE_LOW = "G3"
TEST_NOTE_HIGH = "G5"

# 一批内最大音程跨度（自然音阶的“度数”，如 5 = do～sol）
MAX_DEGREE_SPAN = 8

# t1～t4, n1, n2
T1_NOTE_DURATION = 0.6
T2_NOTE_INTERVAL = 0.2
T3_REPEAT_INTERVAL = 3.2
T4_BATCH_INTERVAL = 3.2
N1_NOTES_PER_BATCH = 8
N2_REPEAT_COUNT = 100
FREQUENCY_TOLERANCE = 1.0
# ============================================================================


def note_name_to_freq(name):
    """音名 -> 频率(Hz)。如 'C4'、'A4'、'F#5'。A4=440Hz。"""
    name = name.strip().upper()
    n = 0
    while n < len(name) and name[n] in 'CDEFGAB':
        n += 1
    if n == 0:
        return MIDDLE_DO_HZ
    note = name[:n]
    rest = name[n:].strip()
    if rest.startswith('#'):
        sharp = 1
        rest = rest[1:].strip()
    else:
        sharp = 0
    try:
        octave = int(rest) if rest else 4
    except ValueError:
        octave = 4
    # C=0, C#=1, D=2, ... B=11
    base = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}.get(note[0], 0)
    semitones = base + sharp
    # A4 = 440 Hz，MIDI 69；C4 = 60
    semitones_from_a4 = (octave - 4) * 12 + (semitones - 9)
    return 440.0 * (2 ** (semitones_from_a4 / 12.0))


# 由音名得到测试频率范围（供内部使用）
TEST_FREQ_MIN = note_name_to_freq(TEST_NOTE_LOW)
TEST_FREQ_MAX = note_name_to_freq(TEST_NOTE_HIGH)

# 八度偏移（+/- 键）
octave_offset = 0
OCTAVE_OFFSET_MIN = -2
OCTAVE_OFFSET_MAX = 2


def build_diatonic_key_map():
    """q～i 低八度八个音，o p l 不发音，a～k 中高八度，z x c v b 高音 do re mi fa sol"""
    key_to_freq = {}
    low_keys = 'qwertyui'
    middle_keys = 'asdfghjk'
    high_keys = ('z', 'x', 'c', 'v', 'b')
    for key in low_keys:
        key_to_freq[key] = LOW_OCTAVE_HZ[low_keys.index(key)]
    for key in SILENT_KEYS:
        pass  # 不加入
    for key in middle_keys:
        key_to_freq[key] = MIDDLE_OCTAVE_HZ[middle_keys.index(key)]
    for key in high_keys:
        key_to_freq[key] = HIGH_DO_RE_MI_FA_SOL_HZ[high_keys.index(key)]
    return key_to_freq


# 键 -> 基础频率（无八度偏移）
KEY_TO_BASE_FREQ = build_diatonic_key_map()


def key_to_frequency(key, octave_shift=0, shift_held=False):
    """根据当前八度偏移和是否按住 Shift 得到该键的频率"""
    if key not in KEY_TO_BASE_FREQ:
        return None
    effective_octave = octave_shift + (1 if shift_held else 0)
    return KEY_TO_BASE_FREQ[key] * (2 ** effective_octave)


# 全局状态
current_batch = None
current_scale_id = None
is_playing = False
is_paused = False
scale_thread = None
start_time = None
skip_remaining_repeats = False
state_lock = threading.Lock()


def frequency_to_note_name(frequency):
    """将频率转换为音符名称"""
    note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    midi_note = 12 * (math.log2(frequency / 440.0)) + 69
    midi_note = round(midi_note)
    octave = (midi_note - 12) // 12
    note_index = midi_note % 12
    note_name = note_names[note_index]
    return f"{note_name}{octave}"


def are_frequencies_match(freq1, freq2, tolerance=FREQUENCY_TOLERANCE):
    return abs(freq1 - freq2) <= tolerance


def get_diatonic_notes_in_range():
    """返回 [TEST_FREQ_MIN, TEST_FREQ_MAX] 内所有自然音阶音的 (freq, linear_degree)。"""
    notes = []
    for oct_rel in range(-3, 4):
        for degree in range(7):
            sem = DIATONIC_SEMITONES[degree]
            freq = MIDDLE_DO_HZ * (2 ** (oct_rel + sem / 12.0))
            if TEST_FREQ_MIN <= freq <= TEST_FREQ_MAX:
                linear = oct_rel * 7 + degree
                notes.append((freq, linear))
    return sorted(notes, key=lambda x: x[0])


def generate_batch():
    """生成一批音符：仅在测试频率范围内，且一批内度数跨度不超过 MAX_DEGREE_SPAN。"""
    global current_batch
    candidates = get_diatonic_notes_in_range()
    if not candidates:
        # 若范围内没有音，则用 C4～C5 白键兜底
        candidates = [(MIDDLE_DO_HZ * (2 ** (s / 12.0)), s) for s in [0, 2, 4, 5, 7, 9, 11]]
        candidates = [(f, 0) for f, _ in candidates if TEST_FREQ_MIN <= f <= TEST_FREQ_MAX]
    if not candidates:
        current_batch = [MIDDLE_DO_HZ]
        return current_batch

    min_lin = min(l for _, l in candidates)
    max_lin = max(l for _, l in candidates)
    span = min(MAX_DEGREE_SPAN, max_lin - min_lin) if max_lin > min_lin else 0
    if span <= 0:
        freqs = [f for f, _ in candidates]
        current_batch = [random.choice(freqs) for _ in range(N1_NOTES_PER_BATCH)]
        return current_batch

    start = random.randint(min_lin, max_lin - span) if (max_lin - span >= min_lin) else min_lin
    end = start + span
    in_span = [(f, l) for f, l in candidates if start <= l <= end]
    if not in_span:
        in_span = candidates
    freqs = [f for f, _ in in_span]
    current_batch = [random.choice(freqs) for _ in range(N1_NOTES_PER_BATCH)]
    return current_batch


def play_batch_loop():
    global current_batch, current_scale_id, is_playing, is_paused, skip_remaining_repeats
    while is_playing:
        if is_paused:
            time.sleep(0.1)
            continue
        with state_lock:
            generate_batch()
            current_scale_id = time.time()
            batch_copy = current_batch.copy()
            skip_remaining_repeats = False
            t1, t2, t3, t4 = T1_NOTE_DURATION, T2_NOTE_INTERVAL, T3_REPEAT_INTERVAL, T4_BATCH_INTERVAL
            n2 = N2_REPEAT_COUNT
        for repeat in range(n2):
            if not is_playing or skip_remaining_repeats:
                break
            for i, freq in enumerate(batch_copy):
                if not is_playing or skip_remaining_repeats:
                    break
                while is_paused and is_playing:
                    time.sleep(0.1)
                if not is_playing:
                    break
                note_key = f"batch_{repeat}_{i}_{time.time()}"
                start_note(note_key, freq, '1')
                time.sleep(t1)
                stop_note(note_key)
                if i < len(batch_copy) - 1:
                    time.sleep(t2)
            if repeat < n2 - 1 and is_playing and not skip_remaining_repeats:
                time.sleep(t3)
        if is_playing:
            time.sleep(t4)


def get_user_input_raw(fd=None, raw_mode=False):
    """获取单字符；返回 (key_lower, shift_held)。"""
    if sys.platform == 'win32':
        import msvcrt
        import ctypes
        VK_SHIFT = 0x10
        if msvcrt.kbhit():
            try:
                key_raw = msvcrt.getch().decode('utf-8')
                shift_held = (ctypes.windll.user32.GetAsyncKeyState(VK_SHIFT) & 0x8000) != 0
                return key_raw.lower(), shift_held
            except Exception:
                return None, False
    else:
        import select
        if not sys.stdin.isatty():
            return None, False
        if raw_mode and fd is not None:
            if select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], []):
                try:
                    key_raw = sys.stdin.read(1)
                    shift_held = key_raw != key_raw.lower() and key_raw.lower() in KEY_TO_BASE_FREQ
                    return key_raw.lower(), shift_held
                except Exception:
                    return None, False
    return None, False


def main():
    global current_batch, current_scale_id, is_playing, is_paused, scale_thread
    global start_time, skip_remaining_repeats, octave_offset

    print("=" * 60)
    print("音高寻找练耳程序 v4 - QWERTY 自然音阶")
    print("=" * 60)
    print("\n📝 说明:")
    print("  • 键盘按 qwertyuiopasdfghjklzxcvb 顺序为自然音阶，a = 中音 do")
    print(f"  • 每批 {N1_NOTES_PER_BATCH} 个随机音符，重复 {N2_REPEAT_COUNT} 次后换批")
    print("  • 测试音范围: {} ~ {} ({:.1f} Hz ~ {:.1f} Hz)".format(
        TEST_NOTE_LOW, TEST_NOTE_HIGH, TEST_FREQ_MIN, TEST_FREQ_MAX))
    print("  • 一批内最大跨度: {} 度".format(MAX_DEGREE_SPAN))
    print("\n⌨️  按键:")
    print("  • 试音: q～i 低八度八个音，o p 不发音，a～k 中高八度(a=中音do k=高音do)，l 不发音，z x c v b=高音 do re mi fa sol")
    print("  • + / -: 整体升八度 / 降八度")
    print("  • 按住 Shift + 试音键: 临时升八度")
    print("  • 空格: 暂停/继续")
    print("  • N: 跳过当前批剩余重复，进入下一批")
    print("  • ESC: 退出")
    print("=" * 60)

    if not init_audio():
        print("错误: 无法初始化音频设备")
        return
    if FLUIDSYNTH_AVAILABLE:
        init_soundfont()

    print("\n准备开始...")
    time.sleep(0.5)

    current_batch = generate_batch()
    current_scale_id = time.time()
    is_playing = True
    start_time = time.time()
    scale_thread = threading.Thread(target=play_batch_loop, daemon=True)
    scale_thread.start()

    pressed_keys = {}
    user_note_keys = {}
    print("\n🎵 批次已开始播放\n")

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
            key, shift_held = get_user_input_raw(fd=fd, raw_mode=True)
            if key is None:
                time.sleep(0.01)
                continue

            try:
                if ord(key) == 27:
                    print("\n\n退出程序...")
                    break
            except Exception:
                pass

            if key == ' ':
                is_paused = not is_paused
                status = "暂停" if is_paused else "继续"
                print(f"\r⏸️  {status}", end='', flush=True)
                continue

            if key == 'n':
                with state_lock:
                    skip_remaining_repeats = True
                print(f"\r⏭️  跳过剩余重复，进入下一批", end='', flush=True)
                continue

            # + 整体升八度
            if key == '+' or key == '=':
                octave_offset = min(octave_offset + 1, OCTAVE_OFFSET_MAX)
                print(f"\r八度: {'+' if octave_offset >= 0 else ''}{octave_offset}", end='', flush=True)
                continue
            # - 整体降八度
            if key == '-' or key == '_':
                octave_offset = max(octave_offset - 1, OCTAVE_OFFSET_MIN)
                print(f"\r八度: {'+' if octave_offset >= 0 else ''}{octave_offset}", end='', flush=True)
                continue

            if key in KEY_TO_BASE_FREQ:
                user_freq = key_to_frequency(key, octave_offset, shift_held)
                if user_freq is None:
                    continue
                if key in user_note_keys:
                    stop_note(user_note_keys[key])
                    del user_note_keys[key]
                    if key in pressed_keys:
                        del pressed_keys[key]
                user_note_key = f"user_{key}_{time.time()}"
                start_note(user_note_key, user_freq, '2')
                user_note_keys[key] = user_note_key
                pressed_keys[key] = time.time()

                match_found = False
                with state_lock:
                    batch_copy = current_batch.copy() if current_batch else None
                if batch_copy:
                    for batch_freq in batch_copy:
                        if are_frequencies_match(user_freq, batch_freq):
                            match_found = True
                            break
                user_note = frequency_to_note_name(user_freq)
                if match_found:
                    print(f"\r✓ {user_note}", end='', flush=True)
                else:
                    print(f"\r{user_note}", end='', flush=True)

            current_time = time.time()
            keys_to_release = [k for k, t in pressed_keys.items() if current_time - t > 1.0]
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
        if sys.platform != 'win32' and original_settings is not None and fd is not None:
            try:
                import termios
                termios.tcsetattr(fd, termios.TCSADRAIN, original_settings)
            except Exception:
                pass
        is_playing = False
        for note_key in list(user_note_keys.values()):
            stop_note(note_key)
        if scale_thread and scale_thread.is_alive():
            scale_thread.join(timeout=1.0)
        cleanup_audio()
        elapsed_time = time.time() - start_time if start_time else 0
        print("\n" + "=" * 60)
        print("练习结束")
        print("=" * 60)
        print(f"时长: {elapsed_time:.0f}秒")
        print("=" * 60)


if __name__ == '__main__':
    main()
