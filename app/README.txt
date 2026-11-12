  ✿  MOCHI POMODORO  ·  v1.0.0  ✿
  Desktop Pomodoro timer
  ----------------------------------------

WHAT IS IT?
  A Pomodoro timer: you work for 25 minutes, rest for 5,
  and every 4 pomodoros you take a long 15-minute break.
  All times can be changed in "settings".


WHAT'S IN THIS .ZIP
  MochiPomodoro.pyw .... the program (a single text file, you can read it)
  README.txt ........... this manual


REQUIREMENT: PYTHON 3.8 OR NEWER (free)
  Windows:
    1. Go to https://www.python.org/downloads/ and download Python.
    2. In the installer, check the box "Add python.exe to PATH".
    3. Leave "tcl/tk and IDLE" checked (it is checked by default).
  macOS:
    Install Python from python.org (it includes tkinter).
  Linux:
    sudo apt install python3 python3-tk   (Debian/Ubuntu)


HOW TO OPEN IT
  1. Unzip the .zip (right-click > "Extract All...").
  2. Open the MochiPomodoro folder.
  3. Windows: double-click MochiPomodoro.pyw
     macOS/Linux: open a terminal in the folder and type
                  python3 MochiPomodoro.pyw

  Double-click does nothing on Windows?
    Right-click the file > Open with > Python.
    Or open PowerShell in the folder and type:  python MochiPomodoro.pyw


HOW TO USE IT
  · Tabs at the top: Focus / Break / Long.
  · Pink button: start or pause.
  · ↺  resets the current timer.
  · »  skips to the next block.
  · The little dots show how many pomodoros you've done in the cycle.
  · When a block ends, a chime plays, the window comes to the front
    and it moves on to the next block by itself (you decide when to start it).
  · "settings": change the focus, break and long break minutes,
    and how many pomodoros come before the long break.
  · "always on top": keeps the window above all others.
  · While running, the time shows in the taskbar.

  Keyboard shortcuts
    Space ........ start / pause
    R ............ reset
    S ............ skip
    1 / 2 / 3 .... Focus / Break / Long


SECURITY AND PRIVACY
  · It's not an .exe: it's plain-text Python code. Open it with Notepad
    and read everything it does, it's about 380 lines.
  · It doesn't use the internet. It doesn't import any network module.
  · It doesn't need administrator permissions and doesn't install anything.
  · It doesn't touch the Windows registry or run at startup.
  · It only writes one file: mochi_settings.json (your minutes), in this
    same folder. You can delete it whenever you want.
  · Check that your file wasn't modified by comparing its SHA-256
    fingerprint with the one published on the download page:
        PowerShell:  Get-FileHash .\MochiPomodoro.pyw -Algorithm SHA256
        macOS/Linux: shasum -a 256 MochiPomodoro.pyw


UNINSTALL
  Delete the MochiPomodoro folder. Done, nothing else is left behind.


  Made with love ♡  ·  time to focus!
