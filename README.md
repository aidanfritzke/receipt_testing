morning_report.bat is triggered every morning at 6am.

it runs morning_report.py which generates a morning_report.txt

then the .bat converts that .txt file into a hex string, then into a binary.

that binary is sent over a usb-printer cable to an EPSON TM-T88IV receipt printer.

the .bat file then deletes all the temp files so it is ready to run again the next day

https://github.com/user-attachments/assets/fe389ced-17db-4eac-a24c-194d46292fe7
