# NSGadget and DS4Gadget for Trinket M0

The source code for the Nintendo Switch Gadget and the Sony PS4 Dual Shock 4
Gadget are located as shown below. Both depend on the NicoHood HID library.

https://github.com/gdsports/NSGadget_HID
https://github.com/gdsports/DS4Gadget_HID

WARNING: The DS4Gadget does not support controller authentication so it
will stop working after about 8 minutes. The MayFlash Magic-S Pro controller
adapter solves this problem.

```
PS4 -- MayFlash adapter -- Trinket M0/DS4Gadget -- Rasperry Pi
```

Compiled programs can be burned into the Trinket M0 just by dragging and
dropping a UF2 file on to the Trinket M0 USB drive. There is no need to install
the Arduino IDE, source code, or USB serial device driver.

* Download the UF2 file.
* Plug in the Trinket M0 to the computer.
* Double tap the Trinket M0 reset button.
* When the TRINKETBOOT USB drive appears, drop the UF2 file on to the drive.
* Wait a few seconds until the Trinket M0 reboots.


