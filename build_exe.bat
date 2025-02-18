@echo off
REM Clean previous build
rmdir /S /Q build
rmdir /S /Q dist

REM 
pyinstaller --clean "Gaming Adaptive Display.spec"
pause