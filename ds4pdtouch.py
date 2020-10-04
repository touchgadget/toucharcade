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
import getopt
import os
import pygame
from pygame.locals import *
import serial
from touchareas import TouchAreas
from ds4gpadserial import DS4GamepadSerial, DS4Button, DPadButton
from nsgpadserial import NSGamepadSerial, NSButton

try:
    opts, args = getopt.getopt(sys.argv[1:], "hslc", ["help", "slider=", "layout=", "console="])
except getopt.GetoptError as err:
    print(err)
    #usage()
    sys.exit(2)
layout = 2
slider = "dedicated"
console = "switch"
for o, a in opts:
    if o in ("-h", "--help"):
        #usage()
        sys.exit()
    elif o in ("-s","--slider"):
        if a in ("n", "normal"):
            slider = "normal"
        elif a in ("d", "dedicated"):
            slider = "dedicated"
    elif o in ("-c","--console"):
        if a in ("p", "ps4"):
            console = "ps4"
    elif o in ("-l","--layout"):
        if a == "3":
            layout = 3
    else:
        assert False, "unhandled option"
print("console=", console, "slider=", slider)

DS4G = DS4GamepadSerial()
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
        print("DS4Gadget serial port not found")
        sys.exit(1)
DS4G.begin(NS_SERIAL)

if not pygame.font:
    print("Warning, fonts disabled")

pygame.init()

#Create a display surface object
DISPLAYSURF = pygame.display.set_mode((0, 0), pygame.FULLSCREEN | pygame.HWSURFACE | pygame.DOUBLEBUF)
(screen_width, screen_height) = DISPLAYSURF.get_size()
screen_width_max = screen_width - 1     # Max pixel co-ord
screen_height_max = screen_height -1    # Max pixel co-ord
pygame.mouse.set_visible(False)
if pygame.font:
    fontDefault = pygame.font.Font(None, 504)
    fontSlider = pygame.font.Font(None, 120)
    fontGamepadButton = pygame.font.Font(None, 36)

class GamepadButtons(TouchAreas):
    """ PS4/DS4 buttons """
    def buttonOn(self, gridcell):
        """ Button touched/pressed """
        if TouchAreas.buttonOn(self, gridcell):
            self.drawCell(gridcell, (0, 128, 128))
            button = gridcell['button']
            if button == DPadButton.UP:
                DS4G.dPadYAxis(0)
            elif button == DPadButton.DOWN:
                DS4G.dPadYAxis(255)
            elif button == DPadButton.LEFT:
                DS4G.dPadXAxis(0)
            elif button == DPadButton.RIGHT:
                DS4G.dPadXAxis(255)
            else:
                DS4G.press(gridcell['button'])

    def buttonOff(self, gridcell):
        """ Button released """
        if TouchAreas.buttonOff(self, gridcell):
            self.drawCell(gridcell, self.bgcolor)
            button = gridcell['button']
            if button == DPadButton.UP or button == DPadButton.DOWN:
                DS4G.dPadYAxis(128)
            elif button == DPadButton.LEFT or button == DPadButton.RIGHT:
                DS4G.dPadXAxis(128)
            else:
                DS4G.release(gridcell['button'])

class SlideBar(TouchAreas):
    """ Project Diva slide bar """
    def __init__(self, topLeft, bottomRight, rows, columns, gridlines, bgcolor, font, properties, displaysurf):
        """ Constructor """
        TouchAreas.__init__(self, topLeft, bottomRight, rows, columns, gridlines, bgcolor, font, properties, displaysurf)
        self.hands = []
        self.handsOld = []

    def buttonOn(self, gridcell):
        """ Button touched/pressed """
        if TouchAreas.buttonOn(self, gridcell):
            self.drawCell(gridcell, (0, 128, 128))
            self.update()

    def buttonOff(self, gridcell):
        """ Button released """
        if TouchAreas.buttonOff(self, gridcell):
            self.drawCell(gridcell, self.bgcolor)
            self.update()

    def fingerMove(self, gridcell, gridcell_new):
        if TouchAreas.buttonOn(self, gridcell_new):
            self.drawCell(gridcell_new, (0, 128, 128))
        if TouchAreas.buttonOff(self, gridcell):
            self.drawCell(gridcell, self.bgcolor)
        self.update()

    def update(self):
        """
        Update the screen for all changed(modified) cells. Also send slider
        bits out to Switch.
        TBD: updating the screen might be increasing latency. Maybe add
        command line option to draw grid but not update screen on touches.
        """
        #entry_ticks = pygame.time.get_ticks()
        slider_bits = 0
        bit_count = 31
        for gridcell in self.cells:
            buttonDown = gridcell['buttonDown']
            if buttonDown > 0:
                slider_bits |= (1 << bit_count)
            bit_count -= 1

        #rect_ticks = pygame.time.get_ticks()
        #print('update_rec', pygame.time.get_ticks() - rect_ticks)
        print('%08x' % (slider_bits))
        #print('update ms', pygame.time.get_ticks() - entry_ticks)
        # Code for tracking hands and hand motion no longer useful but
        # this might be useful for the PS4.
        if slider == "dedicated":
            DS4G.allAxes(slider_bits ^ 0x80808080)
        else:
            num_hands = self.find_hands(slider_bits)
            print('hands', num_hands, self.hands)
            if num_hands == 0:
                DS4G.leftXAxis(128)
                DS4G.rightXAxis(128)
            elif num_hands == 1 and len(self.handsOld) > 0:
                moved = self.detect_motion(self.hands[0], self.handsOld[0])
                print('hand=1, moved=', moved)
                if moved > 0:
                    DS4G.rightXAxis(255)
                elif moved < 0:
                    DS4G.leftXAxis(0)
                else:
                    DS4G.leftXAxis(128)
                    DS4G.rightXAxis(128)
            elif num_hands == 2 and len(self.handsOld) > 1:
                moved = self.detect_motion(self.hands[0], self.handsOld[0])
                print('hand=2, left moved=', moved)
                if moved > 0:
                    DS4G.leftXAxis(255)
                elif moved < 0:
                    DS4G.leftXAxis(0)
                else:
                    DS4G.leftXAxis(128)
                moved = self.detect_motion(self.hands[1], self.handsOld[1])
                print('hand=2, right moved=', moved)
                if moved > 0:
                    DS4G.rightXAxis(255)
                elif moved < 0:
                    DS4G.rightXAxis(0)
                else:
                    DS4G.rightXAxis(128)
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

class BigButtons(TouchAreas):
    """ Big buttons """
    def buttonOn(self, gridcell):
        """ Button touched/pressed """
        if TouchAreas.buttonOn(self, gridcell):
            DS4G.press(gridcell['button'])
            self.drawCell(gridcell, (255, 255, 255))

    def buttonOff(self, gridcell):
        """ Button released """
        if TouchAreas.buttonOff(self, gridcell):
            DS4G.release(gridcell['button'])
            self.drawCell(gridcell, gridcell['color'])

nsbutton_props = [
    {"label": "ZL", "button": NSButton.LEFT_THROTTLE},
    {"label": "L", "button": NSButton.LEFT_TRIGGER},
    {"label": "LSB/L3", "button": NSButton.LEFT_STICK},
    {"label": "Up", "button": DPadButton.UP},
    {"label": "Down", "button": DPadButton.DOWN},
    {"label": "Left", "button": DPadButton.LEFT},
    {"label": "Right", "button": DPadButton.RIGHT},
    {"label": "-", "button": NSButton.MINUS},
    {"label": "Capture", "button": NSButton.CAPTURE},
    {"label": "Home", "button": NSButton.HOME},
    {"label": "+", "button": NSButton.PLUS},
    {"label": "RSB/R3", "button": NSButton.RIGHT_STICK},
    {"label": "R", "button": NSButton.RIGHT_TRIGGER},
    {"label": "ZR", "button": NSButton.RIGHT_THROTTLE}
]
ps4button_props = [
    {"label": "L2", "button": DS4Button.L2},
    {"label": "L1", "button": DS4Button.L1},
    {"label": "L3", "button": DS4Button.L3},
    {"label": "Up", "button": DPadButton.UP},
    {"label": "Down", "button": DPadButton.DOWN},
    {"label": "Left", "button": DPadButton.LEFT},
    {"label": "Right", "button": DPadButton.RIGHT},
    {"label": "Share", "button": DS4Button.SHARE},
    {"label": "Logo", "button": DS4Button.LOGO},
    {"label": "TPad", "button": DS4Button.TPAD},
    {"label": "Options", "button": DS4Button.OPTIONS},
    {"label": "R3", "button": DS4Button.R3},
    {"label": "R1", "button": DS4Button.R1},
    {"label": "R2", "button": DS4Button.R2}
]

if console == 'ps4':
    props = ps4button_props
elif console == 'switch':
    props = nsbutton_props
else:
    props = None

gamepad_buttons = GamepadButtons([0,0], [screen_width_max, (screen_height / 16) - 1], 1, 14, False, (128,128,128), fontGamepadButton, props, DISPLAYSURF)
gamepad_buttons.draw()

# Properties for every cell, that is, 32
SliderProps = [
        {'label': '<'},
        {'label': 'L'},
        {'label': ' '},
        {'label': ' '},
        {'label': 'T'},
        {'label': ' '},
        {'label': 'O'},
        {'label': ' '},
        {'label': 'U'},
        {'label': ' '},
        {'label': 'C'},
        {'label': ' '},
        {'label': 'H'},
        {'label': ' '},
        {'label': ' '},
        {'label': ' '},
        {'label': ' '},
        {'label': 'S'},
        {'label': ' '},
        {'label': 'L'},
        {'label': ' '},
        {'label': 'I'},
        {'label': ' '},
        {'label': 'D'},
        {'label': ' '},
        {'label': 'E'},
        {'label': ' '},
        {'label': 'R'},
        {'label': ' '},
        {'label': ' '},
        {'label': 'R'},
        {'label': '>'},
]
Slider = SlideBar([0,(screen_height/16)], [screen_width_max, (screen_height-screen_width/4)-1], 1, 32, True, (192,192,192), fontSlider, SliderProps, DISPLAYSURF)
Slider.draw()

ps4button_properties = [
    {"label": "X", "buttonColor": [180,201,132], "button": DS4Button.TRIANGLE, "picture": "triangle.png"},
    {"label": "Y", "buttonColor": [225,178,212], "button": DS4Button.SQUARE, "picture": "square.png"},
    {"label": "B", "buttonColor": [143,181,220], "button": DS4Button.CROSS, "picture": "cross.png"},
    {"label": "A", "buttonColor": [213, 62, 31], "button": DS4Button.CIRCLE, "picture": "circle.png"}
]
nsbutton_properties = [
    {"label": "X", "buttonColor": [180,201,132], "button": NSButton.X, "picture": "triangle.png"},
    {"label": "Y", "buttonColor": [225,178,212], "button": NSButton.Y, "picture": "square.png"},
    {"label": "B", "buttonColor": [143,181,220], "button": NSButton.B, "picture": "cross.png"},
    {"label": "A", "buttonColor": [213, 62, 31], "button": NSButton.A, "picture": "circle.png"}
]
if console == "ps4":
    props = ps4button_properties
elif console == "switch":
    props = nsbutton_properties
else:
    props = None
Buttons = BigButtons([0,screen_height-screen_width/4], [screen_width_max, screen_height_max], 1, 4, False, (128,128,128), fontDefault, props, DISPLAYSURF)
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
                cell_x = int(event.x*screen_width_max)
                cell_y = int(event.y*screen_height_max)
                for touch_area in (gamepad_buttons, Slider, Buttons):
                    gridcell = touch_area.touchToCell(cell_x, cell_y)
                    if gridcell != -1:
                        gridcell['myself'].buttonOn(gridcell)
                        fingers[event.finger_id] = gridcell
                        break
            elif event.type == pygame.FINGERUP:
                cell_x = int(event.x*screen_width_max)
                cell_y = int(event.y*screen_height_max)
                for touch_area in (gamepad_buttons, Slider, Buttons):
                    gridcell = touch_area.touchToCell(cell_x, cell_y)
                    if gridcell != -1:
                        gridcell['myself'].buttonOff(gridcell)
                        fingers[event.finger_id] = gridcell
                        break
            elif event.type == pygame.FINGERMOTION:
                cell_x = int(event.x*screen_width_max)
                cell_y = int(event.y*screen_height_max)
                for touch_area in (gamepad_buttons, Slider, Buttons):
                    gridcell_new = touch_area.touchToCell(cell_x, cell_y)
                    if gridcell_new != -1:
                        gridcell = fingers[event.finger_id]
                        if gridcell != -1:
                            if gridcell_new != gridcell:
                                if gridcell['myself'] == Slider and gridcell['myself'] == Slider:
                                    gridcell['myself'].fingerMove(gridcell, gridcell_new)    
                                else:
                                    gridcell['myself'].buttonOff(gridcell)
                                    gridcell_new['myself'].buttonOn(gridcell_new)
                                fingers[event.finger_id] = gridcell_new
                                break
            else:
                if event.type != pygame.VIDEOEXPOSE and event.type != pygame.MULTIGESTURE:
                    print(event)
        #Slider.update()

if __name__ == "__main__":
    main()
