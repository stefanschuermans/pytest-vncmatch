"""
Extension for VNC client object from pytest_vnc to find specific images
on screen.

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

import dataclasses
import json
import os
import numpy
import pytest_vnc
import time
from typing import List, Optional, Tuple
import cv2


@dataclasses.dataclass
class FindResult:
    """
    Result of an image search operation on the VNC screen.
    img -- the image that has been searched
    screen -- screenshot of the VNC screen
    matches -- image with color 1 at each position at which the top-left corner
               of the seach image has been found
    coord_list -- list of coordinates of found images,
                  list of (x left, y top, x right, y bottom)
    """
    img: Optional[numpy.array]
    screen: numpy.array
    matches: Optional[numpy.array] = None
    coord_list: List[Tuple[int, int]] = dataclasses.field(
        default_factory=list)  # list of (left x, top y, right x, bottom y)

    def _write_image(self, imgname: str, img: Optional[numpy.array]):
        """
        Write image "img" to file "imgname" or delete the file if "img" is None.
        """
        if img is None:
            if os.path.exists(imgname):
                os.unlink(imgname)
            return
        cv2.imwrite(imgname, img)

    def output_imgs(self, dirname: str):
        """
        Output the information about the image search result to the directory.
        """
        # make output directory
        os.makedirs(dirname, exist_ok=True)
        # write search image (or delete it) and screen image
        self._write_image(os.path.join(dirname, 'img.png'), self.img)
        self._write_image(os.path.join(dirname, 'screen.png'), self.screen)
        # write coordinates
        with open(os.path.join(dirname, 'coord_list.json'), 'w') as c_l_f:
            json.dump(self.coord_list, c_l_f, indent='  ')
        # if search image and matches available: generate and write found image
        # otherwise: delete found image
        found: Optional[numpy.array] = None
        if self.img is not None and self.matches is not None:
            img_h, img_w, _channels = self.img.shape
            screen_h, screen_w, _channels = self.screen.shape
            # add black border
            matches_border = cv2.copyMakeBorder(self.matches, img_h - 1,
                                                img_h - 1, img_w - 1,
                                                img_w - 1, cv2.BORDER_CONSTANT,
                                                0)
            # filter with filled rectangle of search image size
            matches_mask = cv2.filter2D(matches_border, -1,
                                        numpy.ones((img_h, img_w)))
            # everything that touched the rectangle -> 1, everything else -> 0
            matches_mask = matches_mask.clip(0, 1).astype(numpy.uint8)
            # cut out section of resulting mask at position of original screen
            matches_mask = matches_mask[img_h // 2:img_h // 2 + screen_h,
                                        img_w // 2:img_w // 2 + screen_w]
            # found image: darkened screen with found search images highlighted
            found = self.screen / 2 + cv2.cvtColor(matches_mask,
                                                   cv2.COLOR_GRAY2BGR) * 128
        self._write_image(os.path.join(dirname, 'found.png'), found)


class VNCMatch:
    """
    Wrapper around VNC client object from pytest_vnc to find specific images
    on screen.
    """
    def __init__(self, vnc: pytest_vnc.VNC):
        """
        Initialize VNC screen mathcer object:
        vnc -- VNC client object from pytest_vnc
        """
        self._vnc = vnc

    def _output_and_fail(self, msg: str, fi_res: FindResult):
        """
        Output error information about a failed image search on screen
        to directory and fail.
        msg -- error message
        fi_res -- find result of failed image search
        """
        timestamp = time.strftime('%Y%m%d-%H%M%S')
        dirname = os.path.join(
            'vncmatch_fails', ''.join([c if c.isalnum() else '_'
                                       for c in msg]) + '_' + timestamp)
        fi_res.output_imgs(dirname)
        assert False, f'{msg:s}, see {dirname:s}'

    def find(self, img: Optional[numpy.array] = None) -> FindResult:
        """
        Find the passed image on the VNC screen and return an find object
        with a screenshot of the screen and all the coordinates at which the
        image has been found.
        img -- OpenCV2 image to search
        """
        # capture screen
        screen = cv2.cvtColor(self._vnc.capture(), cv2.COLOR_RGB2BGR)
        fi_res = FindResult(img=img, screen=screen)
        if img is None:
            return fi_res  # no search image -> return screen and no findings
        # find search image on screen
        match_values = cv2.matchTemplate(screen, img, method=cv2.TM_SQDIFF)
        # top-left coordinates of found images have a 1 in the matches image
        fi_res.matches = (match_values <=
                          0.5 * img.shape[0] * img.shape[1]).astype(int)
        # get coordinates of found positions
        # store as list of (x left, y top, x right, y bottom)
        where = numpy.where(fi_res.matches)
        left_top = zip([int(x) for x in where[1]], [int(y) for y in where[0]])
        img_h, img_w, _channels = img.shape
        fi_res.coord_list = [(xl, yt, xl + img_w - 1, yt + img_h - 1)
                             for xl, yt in left_top]
        return fi_res

    def find_img(self, imgname: str) -> FindResult:
        """
        Find an image on the VNC screen and return an find object with a
        screenshot of the screen and all the coordinates at which the image
        has been found.
        imgname -- file name of image to search
        """
        assert os.path.isfile(imgname), f'image file {imgname:s} is missing'
        img = cv2.imread(imgname, cv2.IMREAD_COLOR)
        return self.find(img)

    def expect_single_img(self,
                          imgname: str,
                          timeout: float = 0.0) -> Tuple[int, int]:
        """
        Check that the image is found exactly once on the screen and
        return the location.
        If the image is not found or found multiple times, output error
        information to directory and fail.
        imgname -- file name of image to search
        timeout -- wait for the specified number of seconds for the single
                   image to appear on the screen
        return -- (x, y) of center of image on the screen
        """
        # try while timeout is not expired
        end = time.time() + timeout
        while True:
            # find image
            fi_res = self.find_img(imgname)
            # found -> retun middle coordinate of found image
            if len(fi_res.coord_list) == 1:
                xl, yt, xr, yb = fi_res.coord_list[0]
                return ((xl + xr) // 2, (yt + yb) // 2)
            # timeout expired -> leave loop
            if time.time() > end:
                break
            # wait a bit
            time.sleep(0.1 * timeout)
        # error - either not found or multiple found
        self._output_and_fail(
            'image found multiple times'
            if len(fi_res.coord_list) > 1 else 'image not found', fi_res)