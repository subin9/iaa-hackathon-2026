Output clip5_code.mp4
Set FontSize 12
Source head.tape
Sleep 600ms
Type "# the probe solver: one x1.2 probe gives the segment's best factor, shrunk for sampling noise"
Enter
Sleep 400ms
Type "vim -R -c 'syntax on' -c 'set nu nowrap' +12 part2/probe_overlays.py"
Enter
Sleep 7s
Type ":q"
Enter
Sleep 300ms
Type ".venv/bin/python part2/probe_overlays.py part2/q12_probes.json work/p2/v12c.csv /tmp/v13_raw.csv"
Enter
Sleep 14s
Sleep 5s
