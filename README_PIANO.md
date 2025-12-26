# 钢琴键盘程序

一个简单的命令行程序，通过键盘按键播放钢琴音阶。

## 安装依赖

```bash
pip install -r requirements.txt
```

或者手动安装：

```bash
pip install pyaudio numpy
```

**注意**：在 macOS 上安装 pyaudio 可能需要先安装 portaudio：

```bash
brew install portaudio
pip install pyaudio
```

在 Linux 上可能需要：

```bash
sudo apt-get install portaudio19-dev python3-pyaudio
```

## 使用方法

运行程序：

```bash
python3 piano.py
```

## 按键映射

- **白键**：`A S D F G H J K` 对应 `C D E F G A B C`
- **黑键**：`W E   T Y U` 对应 `C# D#   F# G# A#`
- **高音**：`Q W E R T Y U I O P [ ] \`

按 `ESC` 或 `Ctrl+C` 退出程序。

## 功能特点

- 实时键盘输入响应
- 钢琴音色模拟（带包络）
- 支持多个八度
- 跨平台支持（Windows/macOS/Linux）







