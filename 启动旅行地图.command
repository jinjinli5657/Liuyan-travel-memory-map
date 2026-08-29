#!/bin/bash
# 双击本文件即可在浏览器打开「我的旅行足迹」地图。
# 它会启动一个本地小服务（python 自带，无需联网），保证你的数据稳定存在本机浏览器里。
cd "$(dirname "$0")"
echo "正在启动本地服务（端口 8080）…"
python3 -m http.server 8080 >/dev/null 2>&1 &
sleep 1.5
open "http://localhost:8080/"
