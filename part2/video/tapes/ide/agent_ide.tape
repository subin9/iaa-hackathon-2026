Output agent_ide.mp4
Set FontSize 13
Set Width 1920
Set Height 1080
Set Padding 10
Set Theme "TokyoNight"
Set Shell "bash"
Set TypingSpeed 22ms
Hide
Type "bash ~/projects/iaa-hackathon/part2/video/tapes/ide/ide.sh"
Enter
Sleep 7s
Type "/clear"
Sleep 500ms
Enter
Sleep 2s
Show
Sleep 2s
Type "Run the Part 2 tests with PYTHONPATH=src:part2 .venv/bin/python -m pytest part2/tests -q and tell me in one line whether they pass."
Sleep 500ms
Enter
Wait+Screen@150s /tests pass|passed in/
Sleep 8s
Type "In part2/LOG.md, find the keep rule written for v14 and check with git log that it was committed before the v14 result entry. Answer in three short lines and quote the rule."
Sleep 500ms
Enter
Sleep 45s
Ctrl+B
Type "o"
Sleep 800ms
Type "/v14_cells replaces v13_cells"
Enter
Sleep 300ms
Type "zz"
Sleep 5s
Ctrl+B
Type "o"
Sleep 800ms
Type "From part2/office_premium.py and work/p2/office_final.csv, show the office premium build-up for reference policy M00118569 in four lines."
Sleep 500ms
Enter
Sleep 50s

Sleep 2s
