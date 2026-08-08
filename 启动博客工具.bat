@echo off
chcp 65001 >nul
title Firefly 博客管理工具
cd /d "d:\2\Firefly"
"C:\Users\Administrator\python-sdk\python3.13.2\python.exe" "博客管理工具.py"
if %errorlevel% neq 0 (
    echo.
    echo 启动失败，请检查 Python 是否已安装
    pause
)
