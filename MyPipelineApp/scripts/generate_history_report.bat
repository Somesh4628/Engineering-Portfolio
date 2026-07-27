@echo off
setlocal

:: Define the output file for the report
set "REPORT_FILE=Project_History_Report.md"

echo Generating historical report for MyPipelineApp...

:: Create the main report header
echo # MyPipelineApp Ecosystem - Historical Report > %REPORT_FILE%
echo Generated on: %date% %time% >> %REPORT_FILE%
echo. >> %REPORT_FILE%
echo --- >> %REPORT_FILE%
echo. >> %REPORT_FILE%

:: --- Generate History for the Conductor Project ---
echo ## Project 1: Conductor & Factory >> %REPORT_FILE%
echo. >> %REPORT_FILE%
git log --pretty=format:"- **%h** | %s *(%cr by %an)*" -- config_tool.py conductor_server.py run_cli.bat run_server.bat >> %REPORT_FILE%
echo. >> %REPORT_FILE%
echo. >> %REPORT_FILE%

:: --- Generate History for the Soul Forger Project ---
echo ## Project 2: Soul Forger Engine & Blueprints >> %REPORT_FILE%
echo. >> %REPORT_FILE%
git log --pretty=format:"- **%h** | %s *(%cr by %an)*" -- soul_forger/ "Soul Forger/" >> %REPORT_FILE%
echo. >> %REPORT_FILE%
echo. >> %REPORT_FILE%

:: --- Generate History for the Oracle Engine Project ---
echo ## Project 3: Oracle AI & Simulation Engine >> %REPORT_FILE%
echo. >> %REPORT_FILE%
git log --pretty=format:"- **%h** | %s *(%cr by %an)*" -- "AI ML/" >> %REPORT_FILE%
echo. >> %REPORT_FILE%
echo. >> %REPORT_FILE%

echo.
echo [SUCCESS] Report generated: %REPORT_FILE%
endlocal
