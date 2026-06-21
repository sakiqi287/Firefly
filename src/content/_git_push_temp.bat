@echo off
chcp 65001 >nul
cd /d "D:\2\Firefly\src\content"
echo ============================================
echo   Firefly 博客 Git 推送
echo ============================================
echo.
echo [1/4] git add -A
git add -A
echo.
echo [2/4] git status
git status
echo.
echo [3/4] git commit -m "update"
git commit -m "update"
echo.
echo [4/4] git push
git push
echo.
echo ============================================
echo   完成! 按任意键退出...
echo ============================================
pause >nul
