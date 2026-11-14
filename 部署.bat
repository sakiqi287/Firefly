@echo off
chcp 65001 >nul
title 博客部署工具

echo ========================================
echo   博客部署到 Cloudflare Workers
echo ========================================
echo.

echo [1/2] 构建网站...
call pnpm run build
if %errorlevel% neq 0 (
    echo.
    echo ❌ 构建失败！请检查错误信息。
    pause
    exit /b 1
)

echo.
echo [2/2] 部署到 Cloudflare Workers...
set CLOUDFLARE_API_TOKEN=
if exist "%~dp0cloudflare_token.txt" set /p CLOUDFLARE_API_TOKEN=<"%~dp0cloudflare_token.txt"
if "%CLOUDFLARE_API_TOKEN%"=="" (
    echo.
    echo ❌ 未找到 Cloudflare API Token。
    echo    请在项目根目录创建 cloudflare_token.txt 并写入 Token。
    pause
    exit /b 1
)
call npx wrangler deploy
if %errorlevel% neq 0 (
    echo.
    echo ❌ 部署失败！请检查错误信息。
    pause
    exit /b 1
)

echo.
echo ========================================
echo  ✅ 部署成功！网站已更新。
echo  https://huiyuzi.top
echo ========================================
echo.
pause
