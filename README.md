# pytest-vncmatch

The pytest-vncmatch module is a small extension to pytest-vnc for finding
certain content on the screen in GUI tests based on VNC and pytest. Tests in the style of "find this button, click it, check that something appears on the screen" can be written using this module.

The pytest-vnc module provides functionality to control a VNC session in a test
by simulating mouse actions and keyboard actions as well as capturing the screen
content. The pytest-vncmatch module adds the capbility to search to VNC screen
for certain images on a pixel-by-pixel level. This enables the tests to react
to screen contens and check screen contents.

## Advantages

- True end-to-end GUI testing:
  from mouse/keyboard action to pixels on the screen.
- Usable for all kinds of GUI frameworks.
- Test process observable live via a VNC viewer.
- Output of screenshots when tests fail,
  for post-mortem analysis of screen contents.

## Limitations

- Dependency on visual appearance of the destop environment:
  desktop manager configuration, window manager configuration,
  font sizes, ...
- Requirment to run the GUI under test in VNC.

## Running the Example Test

### Prerequisites

The following packages need to be installed:
- tightvncserver
- tightvncviewer
- xclock
- opencv
- python 3 >= 3.7
- pytest
- pytest-vnc

On a Debian Linux 11.x, the following commands can be executed to install the
prerequisites:

```bash
sudo apt install -y python3 python3-opencv python3-pip python3-pytest \
                    tightvncviewer tightvncserver x11-apps
pip3 install pytest-vnc
```

#### Patching VNC Authentication

There is apparently a small issue with VNC authentication in the version of
pytest-vnc that comes with Debign Linux 11.x in logging in to tightvncserver.

The file `~/.local/lib/python3.9/site-packages/pytest_vnc.py` contains
the following code in line 140.

```python3
des_key = bytes(int(bin(n)[:1:-1], 2) for n in des_key)
```

The code has to be changed by inserting `.ljust(8, '0')`:

```python3
des_key = bytes(int(bin(n)[:1:-1].ljust(8, '0'), 2) for n in des_key)
```

### Setting up VNC

The VNC server must be configured and started. A VNC client must be connected
to the VNC session for the manual step in the demo test.

Run `vncpasswd` to set a password for VNC sessions. The remainder of this
description uses the placeholder `<VNC password>` for this password. Please
replace this placeholder with the chosen password.

Edit `~/.vnc/xstartup` to run a window manager and `xcalc` instead of the
default `/etc/X11/Xsession`.

An example of file contents for running the example test is:

```bash
#!/bin/sh

xrdb "$HOME/.Xresources"
xsetroot -solid grey
#x-terminal-emulator -geometry 80x24+10+10 -ls -title "$VNCDESKTOP Desktop" &
#x-window-manager &
# Fix to make GNOME work
export XKL_XMODMAP_DISABLE=1
#/etc/X11/Xsession

/usr/bin/marco --no-composite &
/usr/bin/xterm &
/usr/bin/xcalc &
```

Start a VNC session:

```bash
vncserver :42
```

Start a VNC viewer to observe the test and interacti with the test:

```bash
vncviewer -passwd ~/.vnc/passwd :42
```

### Configure VNC for pytest-vnc

In the root of the git worktree of the pytest-vncmatch repo (the directory of
this readme file), create a file `pytest.ini` with the following content:

```
[pytest]
vnc_host=localhost
vnc_port=5942
vnc_passwd=<VNC password>
```

### Running the Test

Make sure that you can see the VNC viewer and that the calculator application
is visible on the VNC screen. Also make sure that your mouse pointer is not
over the VNC viewer.

Run the following command (from a terminal that is not running in the VNC
session) to start the test:

```bash
pytest-3 test_xcalc.py
```

The test will move the mouse pointer in the VNC session, click buttons and
type text. The buttons are found by searching for the button image
(`images/button_*.png`) on the screen and the clicking at the middle position
of the image found on the screen. The result of the test is checked by searching
for the expeted image (`images/display_*.png`) to occur on the screen.

One test case (`test_xcalc`) is supposed to pass and another one
(`test_xcalc_fail`) is supposed to fail.

The third test case (`test_xcalc_timeout`) demonstrates how to wait for some
content to appear on the VNC screen. In this demo, the desired content needs to
be created by manual interaction in the VNC viewer for the test case to pass.
When the calculator application shows `999` in the calculator display, click the
`AC` button of the calculator. This will make the `0` appear in the calculator
display and the third test case passes. If the interaction does not happen
within 3 seconds after `999` appearing, the test case will time out and the test
case will fail.

In a real test case, instead of the manual interaction, the application under
test would be running some processing that takes some time and results in the
desired content to appear on the VNC screen.

In total, the expected output of the test is (assuming the manual interaction
has happened within the timeout):

```
============================ test session starts =======================
platform linux -- Python 3.9.2, pytest-6.0.2, py-1.10.0, pluggy-0.13.0
rootdir: /home/stefan/projects/pytest-vncmatch, configfile: pytest.ini
plugins: vnc-1.0.1
collected 3 items

test_xcalc.py .F.                                             [100%]
=============================== FAILURES ===============================
____________________________ test_xcalc_fail ___________________________

...

test_xcalc.py:70:
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
vncmatch.py:186: in expect_single_img
...

E       AssertionError: image not found, see vncmatch_fails/image_not_found_20221106-000717

vncmatch.py:119: AssertionError
======================= short test summary info=========================
FAILED test_xcalc.py::test_xcalc_fail - AssertionError: image not found,
see vncmatch_fails/image_not_found_20221106-000717
===================== 1 failed, 2 passed in 5.50s ======================
```

For each failed test case, the line number of the failure (`test_xcalc.py:70`)
is reported and the error message is printed
(`image not found, see vncmatch_fails/image_not_found_20221106-000717`).
The directory mentioned in the error message contains a screenshot of the VNC
screen (`screen.png`) at the time when the test failed due to an expected
content not being found on the screen. The directory also contains the expected
image (`img.png`), a version of the screenshow with all found occurences
of the image highlighted (`found.png`) and a list of the coordinates of those
found occurences in JSON format (`coord_list.json`).

### Shutting Down the VNC Session

```bash
vncserver --kill :42
```
