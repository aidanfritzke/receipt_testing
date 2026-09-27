@echo off
setlocal
:: Prints whatever you paste or type into this window on the receipt printer.
:: Same printer share and ESC/POS feed + cut bytes as morning_report.bat/.py.

set "PRINTER=\\localhost\EPSONTM-T88IV"
set "JOB=%TEMP%\print_on_demand"

:: The printer expects CP437; make sure pasted text is converted to it.
chcp 437 >nul

:again
echo.
echo Paste or type the text to print.
echo When done: press Enter, then Ctrl+Z, then Enter.   (Ctrl+C quits)
echo ------------------------------------------
copy con "%JOB%.txt" >nul
if not exist "%JOB%.txt" goto again
for %%f in ("%JOB%.txt") do if %%~zf EQU 0 (del "%JOB%.txt" & goto again)

:: Tail bytes: LF LF, ESC d 4 (feed 4 lines), GS V 0 (full cut) - built via
:: certutil because a .bat can't echo raw ESC/GS bytes.
> "%JOB%.hex" echo 0a0a1b64041d5600
certutil -decodehex -f "%JOB%.hex" "%JOB%.cut" >nul
copy /b "%JOB%.txt" + "%JOB%.cut" "%JOB%.bin" >nul

copy /b "%JOB%.bin" "%PRINTER%" >nul && echo Printed. || echo Print FAILED - is %PRINTER% reachable?

del "%JOB%.txt" "%JOB%.hex" "%JOB%.cut" "%JOB%.bin" 2>nul
goto again
