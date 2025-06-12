from serial.tools import list_ports
from pydobotplus import Dobot, CustomPosition, dobotplus
import time

def read_errors(device: Dobot):
    errors = device.get_alarms()
    if len(errors) != 0:
        print('Errors found:')
        for error in errors:
            print(f'  {error}')

available_ports = list_ports.comports()
print(f'available ports: {[x.device for x in available_ports]}')
port = available_ports[0].device
device = Dobot(port=port)
# device.clear_alarms()
print('CURRENT POSE', device.get_pose())

POSITION_A = CustomPosition(x=247, y=-145, z=12, r=80) #oppak
POSITION_A_HIGH = CustomPosition(x=247, y=-145, z=100, r=80) #oppak hoog
POSITION_B = CustomPosition(x=-100, y=-200, z=100, r=-5) #scan locatie

device.move_to(position=POSITION_A_HIGH)
device.move_to(position=POSITION_A)
device.grip(True)
time.sleep(1)  # Wacht even om grip te krijgen
device.move_to(position=POSITION_A_HIGH)
device.move_to(position=POSITION_B)