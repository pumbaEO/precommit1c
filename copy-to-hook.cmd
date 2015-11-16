@echo off

@echo copy current version repo

xcopy .\ibService .\..\..\.git\hooks\ibService\ /Y /E /F
xcopy .\pre-commit .\..\..\.git\hooks\ /Y /F
mkdir .\..\..\.git\hooks\v8Reader
xcopy .\v8Reader\V8Reader.epf .\..\..\.git\hooks\v8Reader\ /Y /F
xcopy .\pyv8unpack.py .\..\..\.git\hooks\ /Y /F
xcopy .\tools\v8unpack.exe .\..\..\.git\hooks\ /Y /F

cd .\..\..\
git config --local core.quotepath false