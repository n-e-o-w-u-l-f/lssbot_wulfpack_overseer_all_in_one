@echo off
setlocal EnableExtensions
echo Stoppe LSS Bot.exe/java/javaw gezielt...
taskkill /F /IM "LSS Bot.exe" /T 2>nul
powershell -NoProfile -ExecutionPolicy Bypass -Command "$patterns=@('lssbot','LSS Bot','lssbot_5'); Get-CimInstance Win32_Process | ? { $_.Name -in @('java.exe','javaw.exe','LSS Bot.exe') } | %% { $cmd=[string]$_.CommandLine; foreach($p in $patterns){ if($cmd -like ('*'+$p+'*')){ Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue } } }"
exit /b 0
