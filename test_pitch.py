#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试音调是否正确"""

import math
import sys

# 标准频率
STANDARD_FREQUENCIES = {
    'C4': 261.63,
    'D4': 293.66,
    'E4': 329.63,
    'F4': 349.23,
    'G4': 392.00,
    'A4': 440.00,
    'B4': 493.88,
    'C5': 523.25,
}

def frequency_to_midi_note(frequency):
    """将频率转换为 MIDI 音符编号"""
    return int(round(12 * math.log2(frequency / 440.0) + 69))

def midi_to_frequency(midi_note):
    """将 MIDI 音符编号转换为频率"""
    return 440.0 * (2 ** ((midi_note - 69) / 12.0))

print("=" * 60)
print("音调测试")
print("=" * 60)
print("\n标准频率 -> MIDI -> 计算频率 -> 误差")
print("-" * 60)

all_correct = True
for note_name, target_freq in STANDARD_FREQUENCIES.items():
    midi = frequency_to_midi_note(target_freq)
    calculated_freq = midi_to_frequency(midi)
    error = abs(calculated_freq - target_freq)
    error_cents = 1200 * math.log2(calculated_freq / target_freq)
    
    status = "✓" if error < 1.0 else "✗"
    if error >= 1.0:
        all_correct = False
    
    print(f"{note_name:3s}: {target_freq:7.2f} Hz -> MIDI {midi:2d} -> {calculated_freq:7.2f} Hz "
          f"误差: {error:5.2f} Hz ({error_cents:+.1f} cents) {status}")

print("-" * 60)
if all_correct:
    print("\n✓ 所有音调转换正确！")
else:
    print("\n✗ 部分音调有误差，可能需要调整")







