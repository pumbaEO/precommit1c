@echo off

@echo copy current version in bootstrap https://github.com/xUnitFor1C/xdd-bootstrap-1C

xcopy .\ibService .\..\..\.git\hooks\ibService\ /Y /E /F
xcopy .\pre-commit .\..\..\.git\hooks\ /Y /F
mkdir .\..\..\.git\hooks\v8Reader
xcopy .\v8Reader\V8Reader.epf .\..\..\.git\hooks\v8Reader\ /Y /F
xcopy .\pyv8unpack.py .\..\..\.git\hooks\ /Y /F

cd .\..\..\
git config --local core.quotepath false