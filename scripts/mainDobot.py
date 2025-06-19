import argparse
from serial.tools import list_ports
from pydobotplus import Dobot, CustomPosition, dobotplus
import time

def read_errors(device: Dobot):
    errors = device.get_alarms()
    if len(errors) != 0:
        print('Errors found:')
        for error in errors:
            print(f'  {error}')

def plaats_blokje(device, plek):
    if plek == "plek1":
        # Vul hier de coördinaten in voor plek1
        device.move_to(x=-2, y=201, z=120, r=80) # Hoog boven de loopband
        device.move_to(x=-2, y=-201, z=5, r=80)
        device.grip(False)
        time.sleep(0.5)  # Wacht even om los te laten
        device.suck(False)
        device.move_to(x=-2, y=-201, z=120, r=80)
    elif plek == "plek2":
        # Vul hier de coördinaten in voor plek2
        device.move_to(x=230, y=32, z=120, r=110) # Hoog boven de loopband)
        device.move_to(x=230, y=32, z=20, r=110)
        device.grip(False)
        time.sleep(0.5)  # Wacht even om los te laten
        device.suck(False)
        device.move_to(x=230, y=32, z=120, r=110)
    else:
        # Onbekend plek
        device.move_to(x=245, y=8, z=120, r=175) # Hoog boven de loopband
        device.move_to(x=245, y=8, z=5, r=175) # laag boven de loopband
        device.grip(False)
        time.sleep(0.5)  # Wacht even om los te laten
        device.suck(False)
        device.move_to(x=245, y=8, z=120, r=80) # Hoog boven de loopband

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--plaats", type=str, required=True, help="Waar moet het blokje geplaatst worden?")
    args = parser.parse_args()

    available_ports = list_ports.comports()
    print(f'available ports: {[x.device for x in available_ports]}')
    port = available_ports[0].device
    device = Dobot(port=port)
    print('CURRENT POSE', device.get_pose())

    plaats_blokje(device, args.plaats)

