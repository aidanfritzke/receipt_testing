@echo off

py morning_report.py
certutil -encodehex "morning_report.txt" "morning_report_hex.txt"
certutil -decodehex "morning_report_hex.txt" "morning_report.bin"
copy /b "morning_report.bin" "\\localhost\EPSONTM-T88IV"
del morning_report.txt
del morning_report_hex.txt
del morning_report.bin
del to-do_list.txt