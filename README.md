# Touchscreen Monitor Arcade Controller

Use a touchscreen monitor as an arcade controller for a Nintendo Switch.

![System Block Diagram](./images/systemoverview.gif)


The following shows the touch areas on the monitor. The top half has the
32 touch slider. The bottom half has four large buttons.

![Touch regions on monitor](./images/touchareas.jpg)

One option is to plug the Switch HDMI out into the touchscreen monitor.
This creates a Switch MegaMix Tap Play mode but on an external monitor.
The system block diagram shows this option.

The other option is to plug the Switch HDMI out into a different monitor (no
touchscreen needed). Plug the touchscreen monitor into the Raspberry Pi HDMI
out so the touch areas are displayed. This is closer to the arcade experience.

In both cases, the touch USB out from the monitor goes to the Pi.

## Hardware

* Nintendo Switch in dock. No hacks or mods.
* Virzen Portable Monitor with 10-point touchscreen 13.3 inch.
* Raspberry Pi 4. Older Pi's including the Pi Zero may also work but have not
  been tested.
* Trinket M0 running NSGadget (Switch compatible gamepad software)
* Optional breadboard, 2x20 breakout adapter, etc.
* Various HDMI and USB cables.

## USB NSGadget
[This section is adapted from the NSGadget_Pi README.md]

NSGadget is an Adafruit Trinket M0 emulating an NS compatible gamepad. The UART
connection between the Pi and NSGadget runs at 2 Mbits/sec. The UART device
name is /dev/ttyAMA0.

|Trinket M0 |Raspberry Pi
|-----------|------------
|BAT        |5V0
|Gnd        |Gnd
|RX(3)      |D15(TXD)

The firmware/ directory has the NSGadget firmware.

Compiled programs can be burned into the Trinket M0 just by dragging and
dropping a UF2 file on to the Trinket M0 USB drive. There is no need to install
the Arduino IDE, source code, or USB serial device driver.

* Download the UF2 file of your choice.
* Plug in the Trinket M0 to the computer.
* Double tap the Trinket M0 reset button.
* When the TRINKETBOOT USB drive appears, drop the UF2 file on to the drive.
* Wait a few seconds until the Trinket M0 reboots.

## Prepare the Pi
[This section and its two subsections are adapted from the NSGadget_Pi README.md]

Install Raspberry Pi OS (formerly known as Raspbian) Buster Desktop. Update to
the latest version.

```
sudo apt update
sudo apt full-upgrade
sudo reboot
```

### Prepare /dev/ttyAMA0

If the Pi has built-in Bluetooth (Pi 3, Pi 3+, Pi 4, Pi zero W) disable
Bluetooth to free up the PL011 UART.

The following is from /boot/overlays/README.

```
Name:   disable-bt
Info:   Disable onboard Bluetooth on Pi 3B, 3B+, 3A+, 4B and Zero W, restoring
        UART0/ttyAMA0 over GPIOs 14 & 15.
        N.B. To disable the systemd service that initialises the modem so it
        doesn't use the UART, use 'sudo systemctl disable hciuart'.
Load:   dtoverlay=disable-bt
```

```
sudo systemctl disable hciuart
sudo nano /boot/config.txt
```
Add `dtoverlay=disable-bt` as the last line of config.txt. Save and exit.

Turn off the login shell on /dev/ttyAMA0. This is necessary even if the Pi does
not have Bluetooth.

```
sudo raspi-config
```

* Select `Interfacing Options`.
* Select `P6 Serial`.
* Disable the login shell.
* Enable the serial interface.
* Exit raspi-config

```
sudo reboot
```
### Installing pygame 2.0.0-dev6

pygame 1.9 does not support the FINGERUP, FINGERDOWN, and FINGERMOTION events
so this is required.

```
sudo apt install python3 python3-pip python3-serial libsdl2-ttf-2.0-0
python3 -m pip install -U pygame==2.0.0.dev6 --user
git clone https://github.com/touchgadget/toucharcade
cd toucharcade
python3 pdtouch.py
```

## Project Diva Touchscreen

```
python3 pdtouch.py
```

Read fingerup, fingerdown, and fingermove events from touchscreen and write
Switch HID gamepad reports out UART. The four big buttons flash when touched.
The slider has touch indicators at the top of the screen.

TBD: Investigate turning off screen updates or breaking out screen updates to a
separate thread. This might reduce lag. I do not see a lag problem but the
lowest lag is always desirable.

## Related projects

See https://github.com/gdsports/NSGadget_Pi for other ways to use a Pi with a
Switch.

To emulate Switch controllers over Bluetooth, see https://github.com/mart1nro/joycontrol.
It would be nice to use this to eliminate the Trinket M0 and all soldering.

