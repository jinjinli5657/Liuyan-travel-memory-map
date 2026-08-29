@echo off
:: 双击本文件即可在浏览器打开「我的旅行足迹」地图（需已安装 Python）。
:: 它会启动一个本地小服务，保证你的数据稳定存在本机浏览器里。
cd /d "%~dp0"
start "" python -m http.server 8080
timeout /t 2 >nul
start "" http://localhost:8080/
