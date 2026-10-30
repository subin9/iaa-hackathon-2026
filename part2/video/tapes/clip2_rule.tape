Output clip2_rule.mp4
Set FontSize 14
Source head.tape
Sleep 600ms
Type "# the keep-or-drop rule is committed before the score comes back"
Enter
Sleep 400ms
Type "git log --date=format-local:'%Y-%m-%d %H:%M UTC' --format='%ad  %s' -4"
Enter
Sleep 2500ms
Type "vim -R -c 'set nu hls' +/'Rule: the higher' part2/LOG.md"
Enter
Sleep 1500ms
Type "zz"
Sleep 5s
Type ":q"
Enter
Sleep 300ms
Type `kaggle competitions submissions iaa-ai-assisted-hackathon-2026-part-2 --csv | python3 part2/video/subs_table.py 40 | grep -E "v13|v12c"`
Enter
Sleep 4s
Sleep 4s
