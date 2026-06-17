@echo off
REM ============================================================================
REM 预提交检查脚本
REM 集成静态验证、选择器质量检查、smoke 测试
REM
REM Usage:
REM   scripts\pre-commit-check.bat [test_directory]
REM
REM Exit Codes:
REM   0 - 所有检查通过
REM   1 - 有错误阻止提交
REM   2 - 有警告但可以提交
REM ============================================================================

setlocal enabledelayedexpansion

REM 设置颜色（Windows 10+）
for /F %%i in ('echo prompt $E ^| cmd') do set "ESC=%%i"
set "RED=%ESC%[31m"
set "GREEN=%ESC%[32m"
set "YELLOW=%ESC%[33m"
set "CYAN=%ESC%[36m"
set "RESET=%ESC%[0m"

echo.
echo ============================================================
echo   🔍 预提交检查
echo ============================================================
echo.

REM 解析参数
set TEST_DIR=%1
if "%TEST_DIR%"=="" set TEST_DIR=tests

REM 检查测试目录是否存在
if not exist "%TEST_DIR%" (
    echo %RED%❌ 测试目录不存在: %TEST_DIR%%RESET%
    exit /b 1
)

echo %CYAN%📁 测试目录: %TEST_DIR%%RESET%
echo.

REM ============================================================================
REM 检查 1: 静态验证
REM ============================================================================
echo %CYAN%[1/3] 静态验证检查...%RESET%

python "%~dp0verify_selectors.py" "%TEST_DIR%"\*.spec.js >nul 2>&1
set STATIC_CHECK=%ERRORLEVEL%

if %STATIC_CHECK% EQU 0 (
    echo    %GREEN%✅ 静态验证通过%RESET%
) else (
    echo    %RED%❌ 静态验证失败%RESET%
    echo.
    echo 请修复以下问题后再提交：
    echo - ref 属性使用
    echo - CSS 类选择器优先使用
    echo - 固定延迟过长
    echo.
    goto :error_exit
)

echo.

REM ============================================================================
REM 检查 2: 选择器质量检查
REM ============================================================================
echo %CYAN%[2/3] 选择器质量检查...%RESET%

python "%~dp0analyze_selector_quality.py" "%TEST_DIR%"\*.spec.js >nul 2>&1
set QUALITY_CHECK=%ERRORLEVEL%

REM 质量检查警告但不禁止单
if %QUALITY_CHECK% EQU 0 (
    echo    %GREEN%✅ 选择器质量良好%RESET%
) else (
    echo    %YELLOW%⚠️  选择器质量不达标（平均分 ^< 6）%RESET%
    echo    建议优化后再提交，但不会阻止提交
    set /a WARNINGS+=1
)

echo.

REM ============================================================================
REM 检查 3: 快速 Smoke 测试（可选）
REM ============================================================================
echo %CYAN%[3/3] 快速 Smoke 测试...%RESET%

REM 检查是否安装了 Playwright
where npx >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo    %YELLOW%⚠️  未找到 Playwright，跳过测试%RESET%
    goto :summary
)

REM 运行 smoke 测试（标记为 @smoke 的测试）
npx playwright test --grep @smoke --reporter=line >nul 2>&1
set TEST_CHECK=%ERRORLEVEL%

if %TEST_CHECK% EQU 0 (
    echo    %GREEN%✅ Smoke 测试通过%RESET%
) else (
    echo    %RED%❌ Smoke 测试失败%RESET%
    echo.
    echo 请修复失败的测试后再提交
    echo 运行以下命令查看详情:
    echo   npx playwright test --grep @smoke
    echo.
    goto :error_exit
)

echo.

REM ============================================================================
REM 总结
REM ============================================================================
:summary
echo ============================================================
echo   📊 检查总结
echo ============================================================

if defined WARNINGS (
    if !WARNINGS! GTR 0 (
        echo    %YELLOW%⚠️  有警告，但可以提交%RESET%
        exit /b 2
    )
)

echo    %GREEN%✅ 所有检查通过，可以提交！%RESET%
echo.
echo ============================================================
exit /b 0

REM ============================================================================
REM 错误退出
REM ============================================================================
:error_exit
echo.
echo ============================================================
echo    %RED%❌ 预提交检查失败，请修复后重试%RESET%
echo ============================================================
exit /b 1
