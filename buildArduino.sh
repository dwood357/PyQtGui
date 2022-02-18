#!/bin/bash
arduino-cli compile -b arduino:avr:uno ~/radar/Arduino/CAN_SHIELD/CAN_SHIELD.ino
arduino-cli upload -v -p /dev/ttyACM0 --fqbn arduino:avr:uno ~/radar/Arduino/CAN_SHIELD/CAN_SHIELD.ino
