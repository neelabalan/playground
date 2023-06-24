@echo off
fzf > fzfile
set /p args=<fzfile
del fzfile
start gvim %args%