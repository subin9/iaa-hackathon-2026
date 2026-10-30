#!/bin/bash
cd ~/projects/iaa-hackathon
export TZ=UTC PYTHONPATH=src:part2
tmux -f $(dirname "$(readlink -f "$0")")/tmux.conf -L vid kill-server 2>/dev/null
tmux -f $(dirname "$(readlink -f "$0")")/tmux.conf -L vid new-session -d -s ide -x 200 -y 56 "vim -u $(dirname "$(readlink -f "$0")")/vimrc -c 'Lexplore' -c 'wincmd l' ${1:-part2/LOG.md}"
tmux -L vid split-window -h -l 47% -t ide "claude --model sonnet --disallowedTools Edit Write NotebookEdit --allowedTools Read Grep Glob \"Bash(PYTHONPATH=src:part2 .venv/bin/python -m pytest:*)\" \"Bash(git log:*)\""
tmux -L vid select-pane -t ide.0 -T " editor "
tmux -L vid select-pane -t ide.1 -T " Claude Code "
exec tmux -L vid attach -t ide
