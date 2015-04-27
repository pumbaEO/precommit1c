mklink ".git/hooks/pre-commit" "%~dp0pre-commit"
mklink ".git/hooks/pyv8unpack.py" "%~dp0pyv8unpack.py"
mklink /J ".git/hooks/ibService" "%~dp0ibService"
mklink /J ".git/hooks/v8Reader" "%~dp0v8Reader"
git config --local core.quotepath false