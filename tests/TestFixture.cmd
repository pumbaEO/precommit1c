@echo off
setlocal

set mainDir=C:\Projects\xDD\precommit1c
	rem set mainDir=%CD%
set path1Cbin="C:\Program Files (x86)\1cv82\8.2.19.68\bin\1cv8.exe"
set testName=Fixture

set testDir=%mainDir%\tests

rd /S /Q %testDir%\testSrc\%testName%
%path1Cbin% /F"%mainDir%\ibService"  /DisableStartupMessages /execute "%mainDir%\V8Reader.epf" /C"decompile;pathtocf;%testDir%\%testName%.epf;pathout;%testDir%\testSrc\%testName%;ЗавершитьРаботуПосле;" 
endlocal