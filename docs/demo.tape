# Records docs/demo.gif. Run from the repo root with the stack up, a fresh SSO session and a clean git tree:
#
#     vhs docs/demo.tape
#
# vhs needs ttyd and ffmpeg on the PATH (https://github.com/charmbracelet/vhs).

Output docs/demo.gif

Set Shell "bash"
Set FontSize 14
Set Width 1200
Set Height 700
Set Padding 16
Set TypingSpeed 40ms
# The real run takes about 80 s; 3x keeps the GIF short. Lower it if the gate beat reads too fast.
Set PlaybackSpeed 3

Type "make demo"
Sleep 500ms
Enter

# The last lineage line is the "mae <number>" row of show_lineage.py (the log lines use "MAE:" or "mae:").
Wait+Screen@300s /mae +[0-9]/
Sleep 4s
