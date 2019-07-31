@echo OFF

set NSIGHT_AGENT=%~dp0
set VENV_BIN=%NSIGHT_AGENT%venv\Scripts

if exist %NSIGHT_AGENT%wheels (
    exit /b
) else (
    %VENV_BIN%\pip wheel --wheel-dir=%NSIGHT_AGENT%wheels APScheduler
    %VENV_BIN%\pip wheel --wheel-dir=%NSIGHT_AGENT%wheels pywin32
    %VENV_BIN%\pip wheel --wheel-dir=%NSIGHT_AGENT%wheels chardet
)

exit /b
