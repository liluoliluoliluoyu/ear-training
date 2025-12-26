#!/usr/bin/env python3
"""测试 SoundFont 是否正常工作"""

import sys
import time

try:
    import fluidsynth
    print("✓ pyFluidSynth 已安装")
except ImportError:
    print("✗ pyFluidSynth 未安装")
    print("运行: pip install pyFluidSynth")
    sys.exit(1)

import os

# 查找 SoundFont 文件
soundfont_paths = [
    os.path.expanduser('~/soundfonts/FluidR3_GM.sf2'),
    'soundfonts/FluidR3_GM.sf2',
    '/usr/share/sounds/sf2/FluidR3_GM.sf2',
]

soundfont_path = None
for path in soundfont_paths:
    if os.path.exists(path):
        soundfont_path = path
        break

if not soundfont_path:
    print("\n✗ 未找到 SoundFont 文件")
    print("\n请下载 SoundFont 文件并放在以下位置之一:")
    for path in soundfont_paths:
        print(f"  - {path}")
    print("\n推荐下载: FluidR3_GM.sf2")
    sys.exit(1)

print(f"✓ 找到 SoundFont: {soundfont_path}")

# 测试初始化
try:
    fs = fluidsynth.Synth()
    print("✓ FluidSynth 对象创建成功")
    
    # 尝试启动
    drivers = ["coreaudio", "pulseaudio", "alsa", "directsound"]
    started = False
    
    for driver in drivers:
        try:
            print(f"尝试使用驱动: {driver}...")
            fs.start(driver=driver)
            print(f"✓ 成功启动，使用驱动: {driver}")
            started = True
            break
        except Exception as e:
            print(f"  ✗ 失败: {e}")
            continue
    
    if not started:
        print("尝试使用默认驱动...")
        fs.start()
        print("✓ 使用默认驱动启动成功")
        started = True
    
    if not started:
        print("✗ 无法启动音频驱动")
        sys.exit(1)
    
    # 加载 SoundFont
    print(f"\n加载 SoundFont: {soundfont_path}")
    sfid = fs.sfload(soundfont_path)
    
    if sfid < 0:
        print("✗ 无法加载 SoundFont 文件")
        sys.exit(1)
    
    print(f"✓ SoundFont 加载成功 (ID: {sfid})")
    
    # 选择程序
    fs.program_select(0, sfid, 0, 0)
    print("✓ 程序选择成功")
    
    # 测试播放
    print("\n测试播放 C4 (MIDI note 60)...")
    fs.noteon(0, 60, 100)
    time.sleep(0.5)
    fs.noteoff(0, 60)
    time.sleep(0.1)
    
    print("✓ 播放测试完成！")
    print("\n如果听到声音，说明 SoundFont 工作正常！")
    
    # 清理
    fs.delete()
    print("\n✓ 测试完成")
    
except Exception as e:
    print(f"\n✗ 错误: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)







