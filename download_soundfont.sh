#!/bin/bash
# SoundFont 下载脚本

echo "正在下载 SoundFont 文件..."
echo ""

SOUNDFONT_DIR="$HOME/soundfonts"
mkdir -p "$SOUNDFONT_DIR"

cd "$SOUNDFONT_DIR"

# 尝试多个下载源
echo "尝试从多个源下载 FluidR3_GM.sf2..."
echo ""

# 源1: SourceForge (如果可用)
echo "尝试源1: SourceForge..."
curl -L --fail --progress-bar -o FluidR3_GM.sf2 \
  "https://sourceforge.net/projects/fluidsynth/files/FluidR3_GM.sf2/download" 2>&1 | grep -E "(Total|%|error)" || true

if [ -f "FluidR3_GM.sf2" ] && [ -s "FluidR3_GM.sf2" ] && file FluidR3_GM.sf2 | grep -q "RIFF\|data"; then
    echo "✓ 下载成功！"
    echo "文件位置: $SOUNDFONT_DIR/FluidR3_GM.sf2"
    exit 0
fi

# 源2: 尝试其他镜像
echo ""
echo "尝试源2: 其他镜像..."
curl -L --fail --progress-bar -o FluidR3_GM.sf2 \
  "http://www.schristiancollins.com/soundfonts/FluidR3_GM.sf2" 2>&1 | grep -E "(Total|%|error)" || true

if [ -f "FluidR3_GM.sf2" ] && [ -s "FluidR3_GM.sf2" ] && file FluidR3_GM.sf2 | grep -q "RIFF\|data"; then
    echo "✓ 下载成功！"
    echo "文件位置: $SOUNDFONT_DIR/FluidR3_GM.sf2"
    exit 0
fi

echo ""
echo "✗ 自动下载失败"
echo ""
echo "请手动下载 SoundFont 文件："
echo "1. 访问以下网站之一："
echo "   - https://member.keymusician.com/Member/FluidR3_GM/"
echo "   - 搜索 'FluidR3_GM.sf2 download'"
echo ""
echo "2. 下载后将文件放在: $SOUNDFONT_DIR/FluidR3_GM.sf2"
echo ""
echo "3. 或者放在项目目录: $(pwd)/soundfonts/FluidR3_GM.sf2"
echo ""
exit 1







