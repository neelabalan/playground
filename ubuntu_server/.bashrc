complete -d cd
bind TAB:menu-complete

VISUAL=vim; export VISUAL EDITOR=vim; export EDITOR
HISTCONTROL=ignoreboth

shopt -s histappend

# for setting history length see HISTSIZE and HISTFILESIZE in bash(1)
HISTSIZE=10000
HISTFILESIZE=2000

if [ -d ~/.bash_completion.d ]; then
  for file in ~/.bash_completion.d/*; do
    . $file
  done
fi

__ps1_startline="\u@\h:[\W]"
__ps1_endline="\[$txtpur\]\[$txtred\] >> \[$txtrst\]"
export PS1="\n\n${__ps1_startline} \n ${__ps1_endline}"


alias tmux='tmux -u'
alias svim='sudo vi'

# enable programmable completion features (you don't need to enable
# this, if it's already enabled in /etc/bash.bashrc and /etc/profile
# sources /etc/bash.bashrc).
if ! shopt -oq posix; then
  if [ -f /usr/share/bash-completion/bash_completion ]; then
    . /usr/share/bash-completion/bash_completion
  elif [ -f /etc/bash_completion ]; then
    . /etc/bash_completion
  fi
fi