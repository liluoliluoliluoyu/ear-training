# SoundFont 设置指南

## 快速开始

### 方法 1: 使用设置脚本（推荐）

```bash
python3 setup_soundfont.py
```

脚本会自动：
- 查找现有的 SoundFont 文件
- 更新 `piano.py` 配置
- 提供下载指引

### 方法 2: 手动设置

1. **下载 SoundFont 文件**

   推荐下载：**FluidR3_GM.sf2** (约 140MB，高质量)
   
   下载地址：
   - https://member.keymusician.com/Member/FluidR3_GM/
   - 或搜索 "FluidR3_GM.sf2 download"

2. **放置文件**

   将下载的 `.sf2` 文件放在以下任一位置（按优先级）：
   
   - `~/soundfonts/FluidR3_GM.sf2` （推荐，用户目录）
   - `soundfonts/FluidR3_GM.sf2` （项目目录）
   - `/usr/share/sounds/sf2/FluidR3_GM.sf2` （系统目录）

3. **运行程序**

   ```bash
   python3 piano.py
   ```

   如果成功加载，会显示：
   ```
   ✓ 已加载 SoundFont: /path/to/FluidR3_GM.sf2
   ✓ 使用真实采样音色！
   ```

## 验证设置

运行测试脚本验证 SoundFont 是否正常工作：

```bash
python3 test_soundfont.py
```

## 故障排除

### 问题：显示"未找到 SoundFont 文件"

**解决方案：**
1. 确认文件已下载且大小 > 1MB
2. 确认文件放在正确位置
3. 运行 `python3 setup_soundfont.py` 检查

### 问题：显示"SoundFont 初始化失败"

**可能原因：**
- FluidSynth 库未安装

**解决方案：**
```bash
# macOS
brew install fluidsynth

# Linux
sudo apt-get install fluidsynth libfluidsynth-dev

# 然后重新安装 Python 包
pip install --force-reinstall pyFluidSynth
```

### 问题：播放时没有声音

**检查：**
1. 系统音量是否打开
2. 音频驱动是否正确（macOS 使用 coreaudio）
3. 查看错误信息

## 其他 SoundFont 资源

除了 FluidR3_GM.sf2，还可以使用：

- **Timbres of Heaven**: https://sourceforge.net/projects/timbresofheaven/
- **Musescore General**: 随 MuseScore 安装
- **其他免费 SoundFont**: 搜索 "free soundfont download"

## 文件大小参考

- 小文件（< 10MB）：音色较少，质量一般
- 中等文件（10-50MB）：平衡的选择
- 大文件（> 100MB）：完整音色库，最佳质量

FluidR3_GM.sf2 约 140MB，包含完整的 GM (General MIDI) 音色库，推荐使用。







