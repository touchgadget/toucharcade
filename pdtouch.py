#!/usr/bin/env python3
"""

Grid of buttons sending USB HID reports
Tested on Raspian python3 pygame 2.0.0 dev6
"""

"""
MIT License

Copyright (c) 2020 touchgadgetdev@gmail.com

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import sys
import pygame
from pygame.locals import *
import serial
from nsgpadserial import NSGamepadSerial, NSButton

NSG = NSGamepadSerial()
try:
    # Raspberry Pi UART on pins 14,15
    NS_SERIAL = serial.Serial('/dev/ttyAMA0', 2000000, timeout=0)
    print("Found ttyAMA0")
except:
    try:
        # CP210x is capable of 2,000,000 bits/sec
        NS_SERIAL = serial.Serial('/dev/ttyUSB0', 2000000, timeout=0)
        print("Found ttyUSB0")
    except:
        print("NSGadget serial port not found")
        sys.exit(1)
NSG.begin(NS_SERIAL)

if not pygame.font:
    print("Warning, fonts disabled")

pygame.init()

#Create a display surface object
DISPLAYSURF = pygame.display.set_mode((0, 0), pygame.FULLSCREEN | pygame.HWSURFACE | pygame.DOUBLEBUF)
(screen_width, screen_height) = DISPLAYSURF.get_size()
pygame.mouse.set_visible(False)
if pygame.font:
    fontDefault = pygame.font.Font(None, 504)

class SlideBar:
    """ Project Diva slide bar """
    def __init__(self, topLeft, bottomRight, rows, columns, gridlines, bgcolor):
        """ Constructor """
        self.topLeft = topLeft
        self.bottomRight = bottomRight
        self.rows = rows
        self.columns = columns
        self.gridLines = gridlines
        self.bgcolor = bgcolor
        self.slidebar = []
        self.hands = []
        self.handsOld = []
        self.cell_height = (bottomRight[1] - topLeft[1]) / rows
        self.cell_width = (bottomRight[0] - topLeft[0]) / columns


    def drawCell(self, rect, color):
        pygame.draw.rect(DISPLAYSURF, color, rect, 0)

    def buttonOn(self, gridcell):
        """ Slide cell touched """
        gridcell['buttonDown'] += 1
        if gridcell['buttonDown'] == 1:
            # dirty means the cell on screen must be updated. Updates are
            # deferred so they can be done more efficiently later in update().
            gridcell['dirty'] = True
            #self.drawCell(gridcell['LEDrect'], (0, 128, 128))

    def buttonOff(self, gridcell):
        """ Slide cell released """
        gridcell['buttonDown'] -= 1
        if gridcell['buttonDown'] == 0:
            gridcell['dirty'] = True
            #self.drawCell(gridcell['LEDrect'], self.bgcolor)

    def draw(self):
        """
        Draw all slider cells.
        Draw grid of size width x height. Each element of the grid is a cell of
        cell_width x cell_height. For example, given a screen size of 1920 x 1080 and a grid 32 cols and 1
        row, cell_width = 1920 / 32 and cell_height = 1080 / 1
        """

        for y in range(self.rows):
            for x in range(self.columns):
                gridcell = {}
                gridcell['myself'] = self
                gridcell["buttonDown"] = 0
                gridcell["buttonDownOld"] = 0
                gridcell['dirty'] = False
                rect = pygame.Rect(self.topLeft[0] + x*self.cell_width,
                        self.topLeft[1] + y*self.cell_height,
                        self.cell_width, self.cell_height)
                gridcell["rect"] = rect
                self.drawCell(rect, self.bgcolor)
                cell_center = (int(x * self.cell_width + self.cell_width/2),
                    int(y * self.cell_height + self.cell_height/2))
                gridcell["button_center"] = cell_center
                LEDrect = pygame.Rect(self.topLeft[0] + x*self.cell_width,
                        self.topLeft[1] + y*self.cell_height,
                        self.cell_width, self.cell_height/8)
                gridcell["LEDrect"] = LEDrect
                self.drawCell(LEDrect, self.bgcolor)
                self.slidebar.append(gridcell)
            if self.gridLines:
                # Draw horizontal grid lines
                pygame.draw.line(DISPLAYSURF, (0, 0, 0),
                        (0, y*self.cell_height), (screen_width-1, y*self.cell_height))
        if self.gridLines:
            # Draw vertical grid lines
            for x in range(self.columns):
                pygame.draw.line(DISPLAYSURF, (0, 0, 0),
                        (x*self.cell_width, 0), (x*self.cell_width, screen_height-1))

    def touchToCell(self, x, y):
        """ Convert touch co-ordinates to cell array offset """
        x = int(x)
        y = int(y)
        if (x >= self.topLeft[0]) and (x <= self.bottomRight[0]) and (y >= self.topLeft[1]) and (y <= self.bottomRight[1]):
            x = int(x / self.cell_width)
            if x >= self.columns:
                x = self.columns-1
            y = int(y / self.cell_height)
            return self.slidebar[y*(self.rows-1) + x]
        return -1

    def update(self):
        """
        Update the screen for all changed(dirty) cells. Also send slider
        bits out to Switch.
        TBD: updating the screen might be increasing latency. Maybe add
        command line option to draw grid but not update screen on touches.
        """
        #entry_ticks = pygame.time.get_ticks()
        slider_bits = 0
        bit_count = 31
        dirty_count = 0
        update_rect = []
        for gridcell in self.slidebar:
            buttonDown = gridcell['buttonDown']
            if gridcell['dirty']:
                dirty_count += 1
                gridcell['dirty'] = False
                if buttonDown != gridcell['buttonDownOld']:
                    rect = gridcell['LEDrect']
                    update_rect.append(rect)
                    if buttonDown > 0:
                        self.drawCell(rect, (0, 128, 128))
                    else:
                        self.drawCell(rect, self.bgcolor)

            if buttonDown > 0:
                slider_bits |= (1 << bit_count)
            bit_count -= 1
            gridcell['buttonDownOld'] = buttonDown

        if dirty_count > 0:
            #rect_ticks = pygame.time.get_ticks()
            pygame.display.update(update_rect)
            #print('update_rec', pygame.time.get_ticks() - rect_ticks)
            print('%08x %d %d' % (slider_bits, dirty_count, len(update_rect)))
            NSG.allAxes(slider_bits ^ 0x80808080)
            #print('update ms', pygame.time.get_ticks() - entry_ticks)
            # Code for tracking hands and hand motion no longer useful but
            # this might be useful for the PS4.
            if False:
                num_hands = self.find_hands(slider_bits)
                print('hands', num_hands, self.hands)
                if num_hands == 0:
                    NSG.leftXAxis(128)
                    NSG.rightXAxis(128)
                elif num_hands == 1 and len(self.handsOld) > 0:
                    moved = self.detect_motion(self.hands[0], self.handsOld[0])
                    print('hand=1, moved=', moved)
                    if moved > 0:
                        NSG.rightXAxis(255)
                    elif moved < 0:
                        NSG.leftXAxis(0)
                    else:
                        NSG.leftXAxis(128)
                        NSG.rightXAxis(128)
                elif num_hands == 2 and len(self.handsOld) > 1:
                    moved = self.detect_motion(self.hands[0], self.handsOld[0])
                    print('hand=2, left moved=', moved)
                    if moved > 0:
                        NSG.leftXAxis(255)
                    elif moved < 0:
                        NSG.leftXAxis(0)
                    else:
                        NSG.leftXAxis(128)
                    moved = self.detect_motion(self.hands[1], self.handsOld[1])
                    print('hand=2, right moved=', moved)
                    if moved > 0:
                        NSG.rightXAxis(255)
                    elif moved < 0:
                        NSG.rightXAxis(0)
                    else:
                        NSG.rightXAxis(128)
                self.handsOld = self.hands

    def detect_motion(self, handsNew, handsOld):
        print(handsNew, handsOld)
        centerNew = ((handsNew['start'] - handsNew['end']) / 2.0) + handsNew['end']
        centerOld = ((handsOld['start'] - handsOld['end']) / 2.0) + handsOld['end']
        print(centerNew, centerOld)
        move = centerOld - centerNew
        if move > 0:
            return 1
        elif move < 0:
            return -1
        else:
            return 0

    def find_hands(self, slider_bits):
        mask = 1 << 31
        hand = {}
        hand_state = 0
        self.hands = []
        for b in range(31, -1, -1):
            if hand_state == 0:
                if slider_bits & mask:
                    hand['start'] = b
                    hand_state = 1
            elif hand_state == 1:
                if (slider_bits & mask) == 0:
                    hand_state = 2
            elif hand_state == 2:
                if (slider_bits & mask) == 0:
                    hand_state = 3
            elif hand_state == 3:
                if (slider_bits & mask) == 0:
                    hand_state = 4
            elif hand_state == 4:
                if (slider_bits & mask) == 0:
                    hand['end'] = b+4
                    hand_state = 0
                    self.hands.append(hand)
                    hand = {}

            mask = mask >> 1
        if hand_state == 1:
            hand['end'] = 0
            self.hands.append(hand)
        elif hand_state == 2:
            hand['end'] = 1
            self.hands.append(hand)
        elif hand_state == 3:
            hand['end'] = 2
            self.hands.append(hand)
        elif hand_state == 4:
            hand['end'] = 3
            self.hands.append(hand)
        return len(self.hands)

Slider = SlideBar([0,0], [screen_width, screen_height/2], 1, 32, True, (192,192,192))
Slider.draw()

class BigButtons:
    """ Big buttons """
    def __init__(self, topLeft, bottomRight, rows, columns, gridlines, bgcolor, properties):
        """ Constructor """
        self.topLeft = topLeft
        self.bottomRight = bottomRight
        self.rows = rows
        self.columns = columns
        self.gridLines = gridlines
        self.bgcolor = bgcolor
        self.buttongrid = []
        self.cell_height = (bottomRight[1] - topLeft[1]) / rows
        self.cell_width = (bottomRight[0] - topLeft[0]) / columns
        self.properties = properties

    def drawCell(self, gridcell, color):
        """ Draw one cell/button """
        rect = gridcell['rect']
        pygame.draw.rect(DISPLAYSURF, color, rect, 0)
        DISPLAYSURF.blit(gridcell['text'], gridcell['textpos'])
        pygame.display.update(rect)

    def buttonOn(self, gridcell):
        """ Button touched/pressed """
        gridcell['buttonDown'] += 1
        if gridcell['buttonDown'] == 1:
            NSG.press(gridcell['nsButton'])
            self.drawCell(gridcell, (255, 255, 255))

    def buttonOff(self, gridcell):
        """ Button released """
        gridcell['buttonDown'] -= 1
        if gridcell['buttonDown'] == 0:
            NSG.release(gridcell['nsButton'])
            self.drawCell(gridcell, gridcell['color'])

    def draw(self):
        """
        Draw all buttons. Usually called only once.
        Draw grid of size width x height. Each element of the grid is a cell of
        cell_width x cell_height. For example, given a screen size of 1920 x 1080 and a grid 32 cols and 1
        row, cell_width = 1920 / 32 and cell_height = 1080 / 1
        """
        button_index = 0
        for y in range(self.rows):
            for x in range(self.columns):
                gridcell = {}
                gridcell['myself'] = self
                gridcell["buttonDown"] = 0
                rect = pygame.Rect(self.topLeft[0] + x*self.cell_width,
                        self.topLeft[1] + y*self.cell_height,
                        self.cell_width, self.cell_height)
                gridcell["rect"] = rect
                cell_center = (self.topLeft[0] + int(x * self.cell_width + self.cell_width/2),
                    self.topLeft[1] + int(y * self.cell_height + self.cell_height/2))
                gridcell["button_center"] = cell_center
                text = fontDefault.render(self.properties[button_index]['label'], 1, (10, 10, 10))
                textpos = text.get_rect(center=cell_center)
                gridcell['text'] = text
                gridcell['textpos'] = textpos
                gridcell['color'] = self.properties[button_index]['buttonColor']
                self.drawCell(gridcell, self.properties[button_index]['buttonColor'])
                gridcell['nsButton'] = self.properties[button_index]['nsButton']
                self.buttongrid.append(gridcell)
                button_index = button_index + 1
            if self.gridLines:
                # Draw horizontal grid lines
                pygame.draw.line(DISPLAYSURF, (0, 0, 0),
                        (0, y*self.cell_height), (screen_width-1, y*self.cell_height))
        if self.gridLines:
            # Draw vertical grid lines
            for x in range(self.columns):
                pygame.draw.line(DISPLAYSURF, (0, 0, 0),
                        (x*self.cell_width, 0), (x*self.cell_width, screen_height-1))

    def touchToCell(self, x, y):
        """ Convert touch co-ordinates to cell """
        x = int(x)
        y = int(y)
        if (x >= self.topLeft[0]) and (x <= self.bottomRight[0]) and (y >= self.topLeft[1]) and (y <= self.bottomRight[1]):
            x = int(x / self.cell_width)
            if x >= self.columns:
                x = self.columns - 1
            y = int(y / self.cell_height)
            return self.buttongrid[y*(self.rows-1) + x]
        return -1

button_properties = [
        {"label": "X", "buttonColor": [180,201,132], "nsButton": 3},
        {"label": "Y", "buttonColor": [225,178,212], "nsButton": 0},
        {"label": "B", "buttonColor": [143,181,220], "nsButton": 1},
        {"label": "A", "buttonColor": [213, 62, 31], "nsButton": 2}
]
Buttons = BigButtons([0,screen_height/2], [screen_width, screen_height], 1, 4, False, (128,128,128), button_properties)
Buttons.draw()

# Up to 10 touches/fingers
fingers = {}

# Update the screen
pygame.display.update()

def main():
    mainLoop = True

    while mainLoop:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                mainLoop = False
            elif event.type == pygame.KEYDOWN:
                if event.key == K_ESCAPE:
                    mainLoop = False
            elif event.type == pygame.FINGERDOWN:
                cell_x = event.x*screen_width
                cell_y = event.y*screen_height
                gridcell = Buttons.touchToCell(cell_x, cell_y)
                if gridcell == -1:
                    gridcell = Slider.touchToCell(cell_x, cell_y)
                if gridcell != -1:
                    gridcell['myself'].buttonOn(gridcell)
                fingers[event.finger_id] = gridcell
            elif event.type == pygame.FINGERUP:
                cell_x = event.x*screen_width
                cell_y = event.y*screen_height
                gridcell = Buttons.touchToCell(cell_x, cell_y)
                if gridcell == -1:
                    gridcell = Slider.touchToCell(cell_x, cell_y)
                if gridcell != -1:
                    gridcell['myself'].buttonOff(gridcell)
                fingers[event.finger_id] = gridcell
            elif event.type == pygame.FINGERMOTION:
                cell_x = event.x*screen_width
                cell_y = event.y*screen_height
                gridcell_new = Slider.touchToCell(cell_x, cell_y)
                if gridcell_new == -1:
                    gridcell_new = Buttons.touchToCell(cell_x, cell_y)
                if gridcell_new != -1:
                    gridcell = fingers[event.finger_id]
                    if gridcell != -1:
                        if gridcell_new != gridcell:
                            gridcell['myself'].buttonOff(gridcell)
                            gridcell_new['myself'].buttonOn(gridcell_new)
                            fingers[event.finger_id] = gridcell_new
        Slider.update()

if __name__ == "__main__":
    main()
