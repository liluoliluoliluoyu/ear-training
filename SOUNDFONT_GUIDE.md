# SoundFont 音色使用指南

## 什么是 SoundFont？

SoundFont 是一种音频采样格式，使用真实乐器录音，音质比合成音色好得多。

## 如何获取 SoundFont 文件

### 推荐的高质量免费 SoundFont：

1. **FluidR3_GM.sf2** (推荐)
   - 下载地址: https://member.keymusician.com/Member/FluidR3_GM/index.html
   - 或搜索 "FluidR3_GM.sf2 download"
   - 大小约 140MB，包含完整的 GM (General MIDI) 音色库

2. **Timbres of Heaven**
   - 下载地址: https://sourceforge.net/projects/timbresofheaven/
   - 高质量，文件较大

3. **Musescore General SoundFont**
   - 下载地址: https://musescore.org/en/handbook/soundfont
   - 中等质量，文件较小

## 安装步骤

### 1. 安装依赖

```bash
pip install pyFluidSynth
```

在 macOS 上可能还需要：
```bash
brew install fluidsynth
```

在 Linux 上：
```bash
sudo apt-get install fluidsynth libfluidsynth-dev
```

### 2. 下载 SoundFont 文件

下载 FluidR3_GM.sf2 或其他 SoundFont 文件

### 3. 设置 SoundFont 路径

有两种方式：

**方式1: 修改代码**
在 `piano.py` 文件中找到：
```python
SOUNDFONT_PATH = None
```
改为：
```python
SOUNDFONT_PATH = "/path/to/your/FluidR3_GM.sf2"
```

**方式2: 放在默认位置**
将 SoundFont 文件放在以下任一位置：
- `~/soundfonts/FluidR3_GM.sf2`
- `soundfonts/FluidR3_GM.sf2` (项目目录下)
- `/usr/share/sounds/sf2/FluidR3_GM.sf2` (系统目录)

程序会自动查找这些位置。

## 使用

运行程序后，如果成功加载 SoundFont，会显示：
```
✓ 已加载 SoundFont: /path/to/file.sf2
使用真实采样音色！
```

如果没有找到，会使用合成音色作为后备。

## 故障排除

1. **找不到 SoundFont**
   - 检查文件路径是否正确
   - 确保文件存在且有读取权限

2. **pyFluidSynth 安装失败**
   - macOS: 先安装 `brew install fluidsynth`
   - Linux: 安装 `sudo apt-get install libfluidsynth-dev`

3. **音频驱动问题**
   - macOS/Linux: 使用 pulseaudio 驱动（默认）
   - Windows: 使用 directsound 驱动（默认）

## 音色对比

- **合成音色**: 快速生成，但音质一般
- **SoundFont**: 真实录音，音质优秀，但需要下载文件

建议使用 SoundFont 获得最佳体验！







