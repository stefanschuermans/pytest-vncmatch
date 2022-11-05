"""
Example of how to use pytest-vncmatch to "test" the X11 application "xcalc".

Copyright 2022 Stefan Schuermans <stefan@schuermans.info>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import os

import vncmatch


def test_xcalc(vnc):
    """
    Test calculating something on xcalc.

    This test assumes that a fresh copy of a plain version of the xcalc
    application in default window size is running on the VNC server and that
    there are no other open windows above it.

    Depending on desktop environment, window manager, font configuration, ...
    it might be needed to update the images used by this test.
    """
    vncm = vncmatch.VNCMatch(vnc)
    # move mouse pointer out of the way (just in case it is just at the
    # wrong position at start an makes screen matching fail)
    vnc.move(0, 0)
    # click some buttons of the calulator
    for button in ('clear', '2', '3', 'plus', '1', '9', 'equals'):
        # find the button of the calculator and click it
        but_x, but_y = vncm.expect_single_img(
            os.path.join('images', f'button_{button:s}.png'))
        vnc.move(but_x, but_y)
        vnc.click()
    # check that the result "42" can be found on the calculator's display
    vncm.expect_single_img(os.path.join('images', 'display_42.png'))


def test_xcalc_fail(vnc):
    """
    Demo of a failing test case.
    
    The "bug" is in the test case, not in xcalc.
    """
    vncm = vncmatch.VNCMatch(vnc)
    # move mouse pointer out of the way (just in case it is just at the
    # wrong position at start an makes screen matching fail)
    vnc.move(0, 0)
    # clear calculator
    but_x, but_y = vncm.expect_single_img(
        os.path.join('images', f'button_clear.png'))
    vnc.move(but_x, but_y)
    vnc.click()
    # type some numbers
    vnc.write('12345')
    # check that the result "42" can be found on the calculator's display,
    # this will fail here, because "12345" has been typed
    vncm.expect_single_img(os.path.join('images', 'display_42.png'))


def test_xcalc_timeout(vnc):
    """
    Demo of a test case with waiting for a certain image to appear within a
    timeout.
    
    This simulated demo test case requires manual interaction to make the test
    pass: When the calculator shows 999 on the VNC screen, click "AC".
    In real cases, the timeout function is for testing actions that take some
    processing time before the result appears on the screen.
    """
    vncm = vncmatch.VNCMatch(vnc)
    # move mouse pointer out of the way (just in case it is just at the
    # wrong position at start an makes screen matching fail)
    vnc.move(0, 0)
    # clear calculator
    but_x, but_y = vncm.expect_single_img(
        os.path.join('images', f'button_clear.png'))
    vnc.move(but_x, but_y)
    vnc.click()
    # type some numbers
    vnc.write('999')
    # check that the display goes back to "0" within 3 seconds,
    # this needs manual interaction for this demo case via a VNC viewer,
    # it will fail the otherwise
    vncm.expect_single_img(os.path.join('images', 'display_0.png'), timeout=3)