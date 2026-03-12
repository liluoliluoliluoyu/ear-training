#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多乐器键盘程序 - 通过键盘按键播放不同乐器的音阶
使用方法：运行程序后，按键盘按键即可播放对应的音阶
按键映射：
  音符键: A S D F G H J K (白键) | W E T Y U (黑键) | Q Z X C V B N M , . / ; ' (高音)
  切换乐器: 1-钢琴 2-吉他 3-小提琴 4-长笛 5-萨克斯 6-电子合成器 7-风琴 8-小号
  + / -: 整体升八度 / 降八度；按住 Shift 再按音符键为临时 +1 八度
  = 然后 1-7: 变调（1=C 2=D 3=E 4=F 5=G 6=A 7=B）
按 ESC 或 Ctrl+C 退出
"""

import sys
import math
import time
import os
import threading
try:
    import pyaudio
    import numpy as np
    # 尝试导入 FluidSynth（用于 SoundFont 音色）
    try:
        import fluidsynth
        FLUIDSYNTH_AVAILABLE = True
    except ImportError:
        FLUIDSYNTH_AVAILABLE = False
        print("提示: 安装 pyFluidSynth 可使用真实采样音色: pip install pyFluidSynth")
except ImportError:
    print("需要安装依赖库：")
    print("pip install pyaudio numpy")
    sys.exit(1)

# 采样率
SAMPLE_RATE = 44100
# 音符持续时间（秒）
NOTE_DURATION = 0.3

# 当前选择的乐器
current_instrument = "钢琴"

# SoundFont 文件路径（如果使用真实采样音色）
# 设置为 None 时，程序会自动在以下位置查找：
# 1. ~/soundfonts/FluidR3_GM.sf2
# 2. soundfonts/FluidR3_GM.sf2 (项目目录)
# 3. /usr/share/sounds/sf2/FluidR3_GM.sf2
SOUNDFONT_PATH = r'/Users/yunyu.yao/soundfonts/FluidR3_GM.sf2'

# FluidSynth 实例
fs = None

# 正在播放的音符跟踪（用于同时播放和长按）
active_notes = {}  # {key: {'midi_note': int, 'thread': Thread, 'stop_event': Event}}
active_notes_lock = threading.Lock()

# 八度偏移：+1 整体升八度，-1 整体降八度
octave_offset = 0
OCTAVE_OFFSET_MIN = -2
OCTAVE_OFFSET_MAX = 2

# 变调：1=C 2=D 3=E 4=F 5=G 6=A 7=B，数字对应半音偏移（相对 C）
KEY_SELECT_SEMITONES = {'1': 0, '2': 2, '3': 4, '4': 5, '5': 7, '6': 9, '7': 11}
KEY_SELECT_NAMES = {'1': 'C', '2': 'D', '3': 'E', '4': 'F', '5': 'G', '6': 'A', '7': 'B'}
SEMITONES_TO_KEY_NAME = {0: 'C', 2: 'D', 4: 'E', 5: 'F', 7: 'G', 9: 'A', 11: 'B'}

# 钢琴键位映射（按键 -> 音符频率）
# 使用科学音高记号法，A4 = 440Hz
KEY_MAP = {
    # 第一个八度 - 白键
    'a': 261.63,  # C4
    's': 293.66,  # D4
    'd': 329.63,  # E4
    'f': 349.23,  # F4
    'g': 392.00,  # G4
    'h': 440.00,  # A4
    'j': 493.88,  # B4
    'k': 523.25,  # C5
    
    # 第一个八度 - 黑键（升调）
    'w': 277.18,  # C#4
    'e': 311.13,  # D#4
    't': 369.99,  # F#4
    'y': 415.30,  # G#4
    'u': 466.16,  # A#4
    
    # 第二个八度 - 白键
    'q': 523.25,  # C5
    'z': 554.37,  # C#5
    'x': 587.33,  # D5
    'c': 622.25,  # D#5
    'v': 659.25,  # E5
    'b': 698.46,  # F5
    'n': 739.99,  # F#5
    'm': 783.99,  # G5
    ',': 830.61,  # G#5
    '.': 880.00,  # A5
    '/': 932.33,  # A#5
    ';': 987.77,  # B5
    "'": 1046.50, # C6
}

# MIDI 程序号映射（用于 SoundFont）
MIDI_PROGRAMS = {
    '1': 0,   # 钢琴 (Acoustic Grand Piano)
    '2': 24,  # 吉他 (Acoustic Guitar (nylon))
    '3': 40,  # 小提琴 (Violin)
    '4': 73,  # 长笛 (Flute)
    '5': 65,  # 萨克斯 (Alto Sax)
    '6': 81,  # 电子合成器 (Lead 1 (square))
    '7': 19,  # 风琴 (Church Organ)
    '8': 56,  # 小号 (Trumpet)
}

# 乐器定义 - 更真实的参数
INSTRUMENTS = {
    '1': {
        'name': '钢琴', 
        'wave': 'sine', 
        'attack': 0.002, 'decay': 0.3, 'sustain': 0.1, 'release': 0.4,
        'harmonics': [1.0, 0.5, 0.25, 0.15, 0.08, 0.04],  # 更多谐波
        'vibrato_rate': 0, 'vibrato_depth': 0,  # 钢琴无颤音
        'brightness_decay': 0.8,  # 高频衰减
        'inharmonicity': 0.001,  # 非谐波性（钢琴弦的物理特性）
        'midi_program': 0
    },
    '2': {
        'name': '吉他', 
        'wave': 'sine', 
        'attack': 0.003, 'decay': 0.2, 'sustain': 0.3, 'release': 0.5,
        'harmonics': [1.0, 0.6, 0.4, 0.25, 0.15, 0.1],
        'vibrato_rate': 5.5, 'vibrato_depth': 0.01,  # 轻微颤音
        'brightness_decay': 0.7,
        'inharmonicity': 0.0005,
        'midi_program': 24
    },
    '3': {
        'name': '小提琴', 
        'wave': 'sine', 
        'attack': 0.15, 'decay': 0.1, 'sustain': 0.85, 'release': 0.3,
        'harmonics': [1.0, 0.7, 0.5, 0.3, 0.2, 0.15, 0.1],
        'vibrato_rate': 6.0, 'vibrato_depth': 0.02,  # 明显颤音
        'brightness_decay': 0.6,
        'inharmonicity': 0.0002,
        'midi_program': 40
    },
    '4': {
        'name': '长笛', 
        'wave': 'sine', 
        'attack': 0.08, 'decay': 0.05, 'sustain': 0.95, 'release': 0.15,
        'harmonics': [1.0, 0.3, 0.15, 0.08],  # 较少谐波
        'vibrato_rate': 5.0, 'vibrato_depth': 0.015,
        'brightness_decay': 0.9,
        'inharmonicity': 0.0001,
        'midi_program': 73
    },
    '5': {
        'name': '萨克斯', 
        'wave': 'sine', 
        'attack': 0.1, 'decay': 0.15, 'sustain': 0.75, 'release': 0.35,
        'harmonics': [1.0, 0.8, 0.6, 0.45, 0.35, 0.25, 0.18],  # 丰富谐波
        'vibrato_rate': 5.5, 'vibrato_depth': 0.018,
        'brightness_decay': 0.5,
        'inharmonicity': 0.0003,
        'midi_program': 65
    },
    '6': {
        'name': '电子合成器', 
        'wave': 'square', 
        'attack': 0.005, 'decay': 0.1, 'sustain': 0.8, 'release': 0.2,
        'harmonics': [1.0, 0.33, 0.2, 0.14, 0.11],
        'vibrato_rate': 0, 'vibrato_depth': 0,
        'brightness_decay': 1.0,
        'inharmonicity': 0,
        'midi_program': 81
    },
    '7': {
        'name': '风琴', 
        'wave': 'sine', 
        'attack': 0.3, 'decay': 0.0, 'sustain': 1.0, 'release': 0.4,
        'harmonics': [1.0, 0.5, 0.33, 0.25, 0.2, 0.17],
        'vibrato_rate': 6.5, 'vibrato_depth': 0.01,  # 风琴颤音
        'brightness_decay': 1.0,
        'inharmonicity': 0,
        'midi_program': 19
    },
    '8': {
        'name': '小号', 
        'wave': 'sine', 
        'attack': 0.08, 'decay': 0.12, 'sustain': 0.8, 'release': 0.25,
        'harmonics': [1.0, 0.7, 0.5, 0.35, 0.25, 0.18, 0.12],
        'vibrato_rate': 0, 'vibrato_depth': 0,
        'brightness_decay': 0.4,  # 明亮音色
        'inharmonicity': 0.0001,
        'midi_program': 56
    },
}

def generate_waveform(frequency, duration, wave_type='sine', sample_rate=SAMPLE_RATE):
    """生成不同波形的音频"""
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    
    if wave_type == 'sine':
        return np.sin(2 * np.pi * frequency * t)
    elif wave_type == 'square':
        return np.sign(np.sin(2 * np.pi * frequency * t))
    elif wave_type == 'sawtooth':
        return 2 * (t * frequency - np.floor(t * frequency + 0.5))
    elif wave_type == 'triangle':
        return 2 * np.abs(2 * (t * frequency - np.floor(t * frequency + 0.5))) - 1
    else:
        return np.sin(2 * np.pi * frequency * t)

def generate_tone(frequency, duration, instrument_key='1', sample_rate=SAMPLE_RATE):
    """
    生成指定频率的音调，使用指定乐器的音色（更真实的物理建模）
    """
    instrument = INSTRUMENTS.get(instrument_key, INSTRUMENTS['1'])
    total_samples = int(sample_rate * duration)
    t = np.linspace(0, duration, total_samples, False)
    
    # 初始化波形
    wave = np.zeros(total_samples)
    
    # 添加颤音（频率调制）
    vibrato = 0
    if instrument.get('vibrato_rate', 0) > 0:
        vibrato = instrument['vibrato_depth'] * np.sin(2 * np.pi * instrument['vibrato_rate'] * t)
    
    # 生成基础波形和谐波（使用非整数倍谐波使音色更真实）
    if 'harmonics' in instrument:
        for i, amplitude in enumerate(instrument['harmonics']):
            if amplitude > 0:
                # 计算实际频率（考虑非谐波性和颤音）
                harmonic_num = i + 1
                inharmonic = instrument.get('inharmonicity', 0) * harmonic_num * harmonic_num
                actual_freq = frequency * harmonic_num * (1 + inharmonic) * (1 + vibrato)
                
                # 生成谐波
                if instrument['wave'] == 'sine':
                    harmonic_wave = np.sin(2 * np.pi * actual_freq * t)
                elif instrument['wave'] == 'square':
                    harmonic_wave = np.sign(np.sin(2 * np.pi * actual_freq * t))
                elif instrument['wave'] == 'sawtooth':
                    harmonic_wave = 2 * (t * actual_freq - np.floor(t * actual_freq + 0.5))
                elif instrument['wave'] == 'triangle':
                    harmonic_wave = 2 * np.abs(2 * (t * actual_freq - np.floor(t * actual_freq + 0.5))) - 1
                else:
                    harmonic_wave = np.sin(2 * np.pi * actual_freq * t)
                
                # 高频衰减（模拟真实乐器的频率响应）
                brightness = instrument.get('brightness_decay', 1.0)
                if harmonic_num > 1:
                    brightness_factor = brightness ** (harmonic_num - 1)
                    amplitude *= brightness_factor
                
                # 谐波包络（高频衰减更快）
                if harmonic_num > 1:
                    harmonic_envelope = np.exp(-t * harmonic_num * 2)  # 高频衰减更快
                    harmonic_wave *= harmonic_envelope
                
                wave += harmonic_wave * amplitude
    
    # 创建更真实的ADSR包络（使用指数曲线）
    attack_samples = int(instrument['attack'] * sample_rate)
    decay_samples = int(instrument['decay'] * sample_rate)
    sustain_level = instrument['sustain']
    release_samples = int(instrument['release'] * sample_rate)
    
    # 确保所有阶段的总和不超过总样本数
    total_adsr_samples = attack_samples + decay_samples + release_samples
    if total_adsr_samples > total_samples:
        # 按比例缩放
        scale = total_samples / total_adsr_samples
        attack_samples = max(1, int(attack_samples * scale))
        decay_samples = max(1, int(decay_samples * scale))
        release_samples = max(1, int(release_samples * scale))
    
    envelope = np.ones(total_samples)
    
    # Attack阶段 - 指数上升（更自然）
    if attack_samples > 0 and attack_samples <= total_samples:
        attack_end = min(attack_samples, total_samples)
        if attack_end > 0:
            attack_t = t[:attack_end]
            if len(attack_t) > 0:
                attack_curve = 1 - np.exp(-attack_t / (instrument['attack'] * 0.3))
                max_attack = np.max(attack_curve)
                if max_attack > 0:
                    attack_curve = attack_curve / max_attack
                envelope[:attack_end] = attack_curve
    
    # Decay阶段 - 指数衰减
    decay_start = attack_samples
    decay_end = min(attack_samples + decay_samples, total_samples - release_samples)
    if decay_end > decay_start and decay_samples > 0:
        decay_t = t[decay_start:decay_end] - t[decay_start]
        if len(decay_t) > 0:
            decay_curve = sustain_level + (1 - sustain_level) * np.exp(-decay_t / (instrument['decay'] * 0.5))
            envelope[decay_start:decay_end] = decay_curve
    
    # Sustain阶段
    sustain_start = decay_end
    sustain_end = max(sustain_start, total_samples - release_samples)
    if sustain_end > sustain_start:
        # Sustain阶段可能有轻微衰减
        sustain_t = t[sustain_start:sustain_end] - t[sustain_start]
        if len(sustain_t) > 0 and (t[sustain_end] - t[sustain_start]) > 0:
            sustain_curve = sustain_level * (1 - 0.1 * sustain_t / (t[sustain_end] - t[sustain_start]))
            envelope[sustain_start:sustain_end] = sustain_curve
        else:
            envelope[sustain_start:sustain_end] = sustain_level
    
    # Release阶段 - 指数衰减
    release_start = max(0, total_samples - release_samples)
    if release_samples > 0 and release_start < total_samples:
        release_t = t[release_start:] - t[release_start]
        if len(release_t) > 0:
            release_curve = sustain_level * np.exp(-release_t / (instrument['release'] * 0.4))
            envelope[release_start:] = release_curve
    
    # 应用包络
    wave = wave * envelope
    
    # 添加微小的随机噪声（模拟真实乐器的细微变化）
    noise_level = 0.001
    noise = np.random.normal(0, noise_level, total_samples)
    wave += noise
    
    # 归一化并转换为16位整数
    max_val = np.max(np.abs(wave))
    if max_val > 0:
        wave = wave / max_val
    
    # 应用轻微的压缩（模拟真实乐器的动态范围）
    wave = np.sign(wave) * (1 - np.exp(-np.abs(wave) * 1.5))
    
    wave = np.int16(wave * 32767 * 0.35)  # 稍微提高音量
    
    return wave

# 全局音频对象
audio_instance = None
audio_stream = None

def init_audio():
    """初始化音频系统"""
    global audio_instance, audio_stream
    try:
        audio_instance = pyaudio.PyAudio()
        audio_stream = audio_instance.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=SAMPLE_RATE,
            output=True
        )
        return True
    except Exception as e:
        print(f"音频初始化错误: {e}")
        return False

def cleanup_audio():
    """清理音频资源"""
    global audio_instance, audio_stream, fs
    try:
        if audio_stream:
            audio_stream.stop_stream()
            audio_stream.close()
        if audio_instance:
            audio_instance.terminate()
        if fs:
            fs.delete()
    except:
        pass

def init_soundfont(soundfont_path=None):
    """初始化 SoundFont（如果可用）"""
    global fs, SOUNDFONT_PATH
    
    if not FLUIDSYNTH_AVAILABLE:
        return False
    
    # 确定 SoundFont 路径
    font_path = None
    if soundfont_path:
        font_path = soundfont_path
    elif SOUNDFONT_PATH and os.path.exists(SOUNDFONT_PATH):
        font_path = SOUNDFONT_PATH
    else:
        # 尝试查找常见的 SoundFont 文件（按优先级排序）
        common_paths = [
            os.path.expanduser('~/soundfonts/FluidR3_GM.sf2'),  # 用户目录（最高优先级）
            os.path.expanduser('~/soundfonts/default.sf2'),  # 默认 SoundFont
            'soundfonts/FluidR3_GM.sf2',  # 项目目录
            'soundfonts/default.sf2',  # 项目目录默认
            '/usr/share/sounds/sf2/FluidR3_GM.sf2',
            '/usr/share/sounds/sf2/default.sf2',
        ]
        for path in common_paths:
            abs_path = os.path.abspath(path)
            if os.path.exists(abs_path):
                file_size = os.path.getsize(abs_path)
                # 检查文件大小（至少100KB才是有效的SoundFont，大文件通常>1MB）
                if file_size > 100 * 1024:  # 100KB
                    # 验证文件格式
                    try:
                        with open(abs_path, 'rb') as f:
                            header = f.read(4)
                            if header.startswith(b'RIFF') or header.startswith(b'sfbk'):
                                font_path = abs_path
                                break
                    except:
                        pass
    
    if not font_path or not os.path.exists(font_path):
        return False
    
    try:
        fs = fluidsynth.Synth(samplerate=SAMPLE_RATE)
        
        # 尝试不同的音频驱动
        drivers = ["coreaudio", "pulseaudio", "alsa", "oss", "directsound"]
        started = False
        last_error = None
        
        for driver in drivers:
            try:
                fs.start(driver=driver)
                started = True
                break
            except Exception as e:
                last_error = e
                continue
        
        if not started:
            # 尝试使用默认驱动
            try:
                fs.start()
                started = True
            except Exception as e:
                last_error = e
        
        if not started:
            raise Exception(f"无法启动音频驱动: {last_error}")
        
        sfid = fs.sfload(font_path)
        if sfid < 0:
            raise Exception(f"无法加载 SoundFont 文件: {font_path}")
        
        SOUNDFONT_PATH = font_path
        fs.program_select(0, sfid, 0, 0)  # 默认使用第一个程序
        
        # 配置音色效果（混响/合唱偏小，减少低音延音、高音更自然）
        try:
            # CC91 = Reverb Send Level (0-127)，偏小减少低音尾音
            fs.cc(0, 91, 16)
            # CC93 = Chorus Send Level (0-127)
            fs.cc(0, 93, 8)
            # CC7 = Volume (0-127)
            fs.cc(0, 7, 100)
            # CC10 = Pan (0-127, 64=center)
            fs.cc(0, 10, 64)
        except:
            # 如果某些设置不支持，忽略错误
            pass
        
        return True
    except Exception as e:
        print(f"SoundFont 初始化失败: {e}")
        if fs:
            try:
                fs.delete()
            except:
                pass
            fs = None
        return False
    
    return False

def frequency_to_midi_note(frequency):
    """将频率转换为 MIDI 音符编号（更精确）"""
    # A4 = 440 Hz = MIDI note 69
    # 使用更精确的计算并四舍五入
    midi = 12 * math.log2(frequency / 440.0) + 69
    return int(round(midi))

def start_note(key, frequency, instrument_key='1'):
    """开始播放音符（非阻塞，支持同时播放多个音符）"""
    global audio_stream, fs, active_notes
    
    # 如果音符已经在播放，不重复播放
    with active_notes_lock:
        if key in active_notes:
            return
    
    # 优先使用 SoundFont（如果可用）
    if fs and FLUIDSYNTH_AVAILABLE:
        try:
            instrument = INSTRUMENTS.get(instrument_key, INSTRUMENTS['1'])
            midi_program = instrument.get('midi_program', 0)
            midi_note = frequency_to_midi_note(frequency)
            
            # 根据乐器调整力度
            velocity_map = {
                '1': 90, '2': 85, '3': 95, '4': 80,
                '5': 100, '6': 90, '7': 85, '8': 95,
            }
            velocity = velocity_map.get(instrument_key, 90)
            # 按音高微调力度：低音略减减少延音感，高音略减更自然
            if midi_note < 52:
                velocity = max(40, int(velocity * 0.88))
            elif midi_note > 84:
                velocity = max(50, int(velocity * 0.9))
            
            # 设置乐器
            fs.program_change(0, midi_program)
            
            # 设置效果（只在第一次）
            try:
                if not hasattr(start_note, '_effects_set'):
                    fs.cc(0, 91, 16)  # Reverb 偏小
                    fs.cc(0, 93, 8)   # Chorus 偏小
                    fs.cc(0, 7, 100)  # Volume
                    start_note._effects_set = True
            except:
                pass
            
            # 确保MIDI音符在有效范围内
            if midi_note < 0:
                midi_note = 0
            elif midi_note > 127:
                midi_note = 127
            
            # 开始播放音符（非阻塞）
            fs.noteon(0, midi_note, velocity)
            
            # 记录正在播放的音符
            with active_notes_lock:
                active_notes[key] = {
                    'midi_note': midi_note,
                    'frequency': frequency,
                    'instrument_key': instrument_key
                }
            
            return
        except Exception as e:
            if not hasattr(start_note, '_error_shown'):
                print(f"SoundFont 播放错误: {e}，使用合成音色")
                start_note._error_shown = True
    
    # 使用合成音色（需要线程）
    def play_synthetic():
        try:
            if not audio_stream:
                if not init_audio():
                    return
            
            # 生成并播放音调（循环播放直到停止）
            while True:
                with active_notes_lock:
                    if key not in active_notes:
                        break
                
                tone = generate_tone(frequency, 0.1, instrument_key)  # 短片段
                audio_stream.write(tone.tobytes())
                time.sleep(0.05)  # 小延迟，避免CPU占用过高
        except:
            pass
        finally:
            with active_notes_lock:
                if key in active_notes:
                    del active_notes[key]
    
    thread = threading.Thread(target=play_synthetic, daemon=True)
    thread.start()
    
    with active_notes_lock:
        active_notes[key] = {
            'thread': thread,
            'frequency': frequency,
            'instrument_key': instrument_key
        }

def stop_note(key):
    """停止播放音符"""
    global fs, active_notes
    
    with active_notes_lock:
        if key not in active_notes:
            return
        
        note_info = active_notes[key]
        
        # SoundFont 方式
        if 'midi_note' in note_info:
            try:
                fs.noteoff(0, note_info['midi_note'])
            except:
                pass
        
        # 合成音色方式（线程会自动停止）
        del active_notes[key]

def play_tone(frequency, duration=NOTE_DURATION, instrument_key='1'):
    """播放指定频率的音调（兼容旧接口，但推荐使用 start_note/stop_note）"""
    # 使用临时key
    temp_key = f"_temp_{time.time()}"
    start_note(temp_key, frequency, instrument_key)
    time.sleep(duration)
    stop_note(temp_key)

def main():
    """主程序"""
    global current_instrument, octave_offset
    
    print("=" * 60)
    print("多乐器键盘程序")
    print("=" * 60)
    print("\n音符按键:")
    print("  白键: A S D F G H J K")
    print("  黑键: W E   T Y U")
    print("  高音: Q Z X C V B N M , . / ; '")
    print("\n切换乐器 (1-8):")
    for key, inst in INSTRUMENTS.items():
        marker = " <--" if inst['name'] == current_instrument else ""
        print(f"  {key} - {inst['name']}{marker}")
    print("\n+/- 键: 整体升八度 / 降八度")
    print("按住 Shift + 音符键: 临时升八度")
    print("= 然后 1-7: 变调 (1=C 2=D 3=E 4=F 5=G 6=A 7=B)")
    print("按 ESC 或 Ctrl+C 退出")
    print("=" * 60)
    
    # 初始化音频
    if not init_audio():
        print("错误: 无法初始化音频设备")
        return
    
    # 尝试初始化 SoundFont
    using_soundfont = False
    if FLUIDSYNTH_AVAILABLE:
        print("\n正在尝试加载 SoundFont 音色...")
        if init_soundfont():
            using_soundfont = True
            print(f"✓ 已加载 SoundFont: {SOUNDFONT_PATH}")
            print("✓ 使用真实采样音色！")
        else:
            print("✗ 未找到 SoundFont 文件，使用合成音色")
            print("\n" + "="*60)
            print("要使用真实采样音色，请下载 SoundFont 文件：")
            print("="*60)
            print("\n1. 下载推荐文件: FluidR3_GM.sf2")
            print("   搜索: 'FluidR3_GM.sf2 download'")
            print("   或访问: https://member.keymusician.com/Member/FluidR3_GM/")
            print("\n2. 设置文件路径（两种方式）:")
            print("   方式A: 在 piano.py 中修改:")
            print("          SOUNDFONT_PATH = '/完整路径/FluidR3_GM.sf2'")
            print("   方式B: 将文件放在以下任一位置:")
            print("          ~/soundfonts/FluidR3_GM.sf2")
            print("          soundfonts/FluidR3_GM.sf2 (项目目录)")
            print("\n3. 重新运行程序")
            print("="*60)
    else:
        print("\n" + "="*60)
        print("要使用真实采样音色，请安装依赖：")
        print("="*60)
        print("1. macOS: brew install fluidsynth")
        print("2. pip install pyFluidSynth")
        print("3. 下载 SoundFont 文件（见上方说明）")
        print("="*60)
    
    current_instrument_key = '1'
    transpose_semitones = 0   # 默认 C 调
    waiting_for_key_select = False
    
    print(f"\n当前乐器: {current_instrument}")
    print(f"当前八度: {'+' if octave_offset >= 0 else ''}{octave_offset} (+/- 可调节)")
    print(f"当前调: {SEMITONES_TO_KEY_NAME.get(transpose_semitones, 'C')}调 (= 后按 1-7 可改)")
    print("就绪，开始演奏...\n")
    
    try:
        if sys.platform == 'win32':
            import msvcrt
            import ctypes
            VK_SHIFT = 0x10
            
            pressed_keys = {}  # {key: last_press_time}
            key_repeat_threshold = 0.15  # 150ms内重复按键认为是长按
            
            while True:
                if msvcrt.kbhit():
                    key_raw = msvcrt.getch().decode('utf-8')
                    shift_held = (ctypes.windll.user32.GetAsyncKeyState(VK_SHIFT) & 0x8000) != 0
                    key = key_raw.lower()
                    current_time_win = time.time()
                    
                    if key == '\x1b':  # ESC
                        if waiting_for_key_select:
                            waiting_for_key_select = False
                        else:
                            for k in list(pressed_keys.keys()):
                                stop_note(k)
                            break
                    
                    # = 键：进入变调选择，再按 1-7 选调
                    if key == '=':
                        waiting_for_key_select = True
                        print("\n请按 1-7 选择调: 1=C 2=D 3=E 4=F 5=G 6=A 7=B")
                        continue
                    if waiting_for_key_select:
                        if key in KEY_SELECT_SEMITONES:
                            transpose_semitones = KEY_SELECT_SEMITONES[key]
                            print(f"\n变调: {KEY_SELECT_NAMES[key]}调")
                            waiting_for_key_select = False
                        else:
                            waiting_for_key_select = False
                        continue
                    
                    # + 键：整体升八度
                    if key == '+':
                        octave_offset = min(octave_offset + 1, OCTAVE_OFFSET_MAX)
                        print(f"\n八度: {'+' if octave_offset >= 0 else ''}{octave_offset}")
                        continue
                    # - 键：整体降八度
                    if key == '-' or key == '_':
                        octave_offset = max(octave_offset - 1, OCTAVE_OFFSET_MIN)
                        print(f"\n八度: {'+' if octave_offset >= 0 else ''}{octave_offset}")
                        continue
                    
                    # 切换乐器
                    if key in INSTRUMENTS:
                        # 停止所有音符
                        for k in list(pressed_keys.keys()):
                            stop_note(k)
                        pressed_keys.clear()
                        current_instrument_key = key
                        current_instrument = INSTRUMENTS[key]['name']
                        print(f"\n切换到: {current_instrument}")
                    
                    # 处理音符按键
                    elif key in KEY_MAP:
                        if key in pressed_keys:
                            # 按键已经在播放
                            last_time = pressed_keys[key]
                            time_since_last = current_time_win - last_time
                            
                            # 如果间隔很短（< 150ms），认为是长按的重复字符，只更新时间戳
                            if time_since_last < key_repeat_threshold:
                                pressed_keys[key] = current_time_win
                                continue  # 不重新播放，保持持续播放
                            else:
                                # 间隔较长，认为是新的按键，停止并重新开始
                                stop_note(key)
                        
                        # 开始播放新音符（八度 + 变调 + Shift 临时升八度）
                        effective_octave = octave_offset + (1 if shift_held else 0)
                        frequency = KEY_MAP[key] * (2 ** (effective_octave + transpose_semitones / 12.0))
                        start_note(key, frequency, current_instrument_key)
                        pressed_keys[key] = current_time_win
                    else:
                        # 按键释放或其他按键
                        if key in pressed_keys:
                            stop_note(key)
                            del pressed_keys[key]
                else:
                    # 检查超时的按键（认为已释放）
                    current_time_win = time.time()
                    keys_to_release = []
                    for k, press_time in pressed_keys.items():
                        if current_time_win - press_time > 0.5:  # 0.5秒超时
                            keys_to_release.append(k)
                    
                    for k in keys_to_release:
                        stop_note(k)
                        del pressed_keys[k]
                    
                    time.sleep(0.01)
        else:
            # Unix/Linux/Mac 使用 termios
            try:
                import termios
                import tty
                
                fd = sys.stdin.fileno()
                
                # 检查是否是终端
                if not sys.stdin.isatty():
                    print("警告: 这不是交互式终端，无法接收键盘输入")
                    print("请在真实终端中运行: Terminal.app -> cd /Users/yunyu.yao/cursor/yyy && source venv/bin/activate && python3 piano.py")
                    return
                
                old_settings = termios.tcgetattr(fd)
                current_instrument_key = '1'  # 初始化乐器键
                
                try:
                    tty.setraw(sys.stdin.fileno())
                    
                    # 按键状态跟踪 {key: last_press_time}
                    pressed_keys = {}
                    key_repeat_threshold = 0.15  # 150ms内重复按键认为是长按
                    key_timeout = 0.5  # 如果0.5秒内没有检测到按键，认为已释放
                    
                    # 使用非阻塞输入
                    import select
                    
                    while True:
                        try:
                            current_time = time.time()
                            
                            # 检查是否有输入（非阻塞）
                            if select.select([sys.stdin], [], [], 0.01)[0]:
                                key_raw = sys.stdin.read(1)
                                # 大写字母表示按住 Shift，临时 +1 八度
                                shift_held = key_raw != key_raw.lower() and key_raw.lower() in KEY_MAP
                                key = key_raw.lower()
                                
                                if ord(key) == 27:  # ESC
                                    if waiting_for_key_select:
                                        waiting_for_key_select = False
                                    else:
                                        for k in list(pressed_keys.keys()):
                                            stop_note(k)
                                        break
                                elif ord(key) == 3:  # Ctrl+C
                                    for k in list(pressed_keys.keys()):
                                        stop_note(k)
                                    break
                                
                                # = 键：进入变调选择，再按 1-7 选调
                                if key == '=':
                                    waiting_for_key_select = True
                                    print("\n请按 1-7 选择调: 1=C 2=D 3=E 4=F 5=G 6=A 7=B")
                                    continue
                                if waiting_for_key_select:
                                    if key in KEY_SELECT_SEMITONES:
                                        transpose_semitones = KEY_SELECT_SEMITONES[key]
                                        print(f"\n变调: {KEY_SELECT_NAMES[key]}调")
                                        waiting_for_key_select = False
                                    else:
                                        waiting_for_key_select = False
                                    continue
                                
                                # + 键：整体升八度
                                if key == '+':
                                    octave_offset = min(octave_offset + 1, OCTAVE_OFFSET_MAX)
                                    print(f"\n八度: {'+' if octave_offset >= 0 else ''}{octave_offset}")
                                    continue
                                # - 键：整体降八度
                                if key == '-' or key == '_':
                                    octave_offset = max(octave_offset - 1, OCTAVE_OFFSET_MIN)
                                    print(f"\n八度: {'+' if octave_offset >= 0 else ''}{octave_offset}")
                                    continue
                                
                                # 切换乐器
                                if key in INSTRUMENTS:
                                    # 停止所有音符
                                    for k in list(pressed_keys.keys()):
                                        stop_note(k)
                                    pressed_keys.clear()
                                    current_instrument_key = key
                                    current_instrument = INSTRUMENTS[key]['name']
                                    print(f"\n切换到: {current_instrument}")
                                
                                # 处理音符按键
                                elif key in KEY_MAP:
                                    if key in pressed_keys:
                                        # 按键已经在播放
                                        last_time = pressed_keys[key]
                                        time_since_last = current_time - last_time
                                        
                                        # 如果间隔很短（< 150ms），认为是长按的重复字符，只更新时间戳
                                        if time_since_last < key_repeat_threshold:
                                            pressed_keys[key] = current_time
                                            continue  # 不重新播放，保持持续播放
                                        else:
                                            # 间隔较长，认为是新的按键，停止并重新开始
                                            stop_note(key)
                                    
                                    # 开始播放新音符（八度 + 变调 + Shift 临时升八度）
                                    effective_octave = octave_offset + (1 if shift_held else 0)
                                    frequency = KEY_MAP[key] * (2 ** (effective_octave + transpose_semitones / 12.0))
                                    start_note(key, frequency, current_instrument_key)
                                    pressed_keys[key] = current_time
                            
                            # 检查超时的按键（认为已释放）
                            keys_to_release = []
                            for k, press_time in pressed_keys.items():
                                if current_time - press_time > key_timeout:
                                    keys_to_release.append(k)
                            
                            for k in keys_to_release:
                                stop_note(k)
                                del pressed_keys[k]
                                
                        except Exception as e:
                            print(f"读取输入错误: {e}")
                            break
                finally:
                    try:
                        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
                    except:
                        pass
            except ImportError:
                print("错误: 无法导入 termios 模块")
                print("请确保在 Unix/Linux/macOS 系统上运行")
            except Exception as e:
                print(f"终端设置错误: {e}")
                print("提示: 请在真实的终端窗口中运行此程序，而不是在IDE的集成终端中")
                
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"\n错误: {e}")
        print("如果遇到问题，请确保已安装依赖：pip install pyaudio numpy")
    finally:
        # 清理音频资源
        cleanup_audio()
    
    print("\n程序已退出。")

if __name__ == "__main__":
    main()

