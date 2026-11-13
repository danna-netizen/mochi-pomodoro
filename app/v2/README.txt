  ✿  MOCHI POMODORO  ·  v2.0.0  ·  matcha latte edition  ✿
  Desktop focus timer
  ----------------------------------------

WHAT IS IT?
  A focus timer with a little mochi that keeps you company.
  Choose your flow (classic Pomodoro, Deep Flow, Soft Start or your own
  minutes), dress up your mochi, and watch your calendar fill with
  matcha-green days.


WHAT'S IN THIS .ZIP
  MochiPomodoro.pyw ....... the program (a single text file, you can read it)
  README.txt .............. this manual
  WHATS-NEW-v2.pdf ........ what changed in version 2


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
  The bar at the bottom has four screens:

  timer  · Tabs at the top: Focus / Break / Long.
         · Big button: start or pause.  ↺ resets  ·  » skips.
         · The dots show your progress in the cycle, and
           "today: 2 / 4 flows" shows your daily goal.
  flow   · Pick how you want to focus:
             Mochi Pomodoro .. 25 focus · 5 break · long every 4
             Deep Flow ....... 50 focus · 10 break · long every 3
             Soft Start ...... 15 focus · 3 break · for slow days
             Your Flow ....... your own focus and break minutes
           (changing the minutes selects "Your Flow" by itself)
         · Daily goal: how many focus blocks make a "done" day.
         · Always on top: keeps the window above the others.
  mochi  · 7 flavors: matcha, sakura, taro, hojicha, yuzu,
           black sesame and milk.  4 toppings: sprout, sakura
           flower, bow or nothing.  The timer takes your mochi's color.
  days   · A calendar of your flow:
             matcha green ... goal reached
             soft green ..... some flow that day
             soft pink ...... not this time (you stopped a block
                              after working on it for 1+ minute)
           Click a day to see its flows and minutes.
           At the bottom: this month's total and your streak.

  Keyboard shortcuts
    Space ........ start / pause
    R ............ reset
    S ............ skip
    1 / 2 / 3 .... Focus / Break / Long
    T F M C ...... Timer / Flow / Mochi / Calendar


SECURITY AND PRIVACY
  · It's not an .exe: it's plain-text Python code. Open it with Notepad
    and read everything it does.
  · It doesn't use the internet. It doesn't import any network module.
  · It doesn't need administrator permissions and doesn't install anything.
  · It doesn't touch the Windows registry or run at startup.
  · It saves your data in this same folder:
        mochi_settings.json ..... your flow, minutes and mochi
        mochi_days.json ......... your calendar
    Delete them whenever you want to start fresh.
  · Coming from v1? Copy your old mochi_settings.json into this folder
    and your minutes become "Your Flow".
  · Check that your file wasn't modified by comparing its SHA-256
    fingerprint with the one published on the download page:
        PowerShell:  Get-FileHash .\MochiPomodoro.pyw -Algorithm SHA256
        macOS/Linux: shasum -a 256 MochiPomodoro.pyw


UNINSTALL
  Delete the MochiPomodoro folder. Done.


  Made with love ♡  ·  stay in your flow!
