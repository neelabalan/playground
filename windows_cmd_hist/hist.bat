@echo off
doskey /history > history
fzf < history > output
set /p args=<output
del history
del output
cmd /C %args%