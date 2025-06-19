from serial.tools import list_ports
from pydobotplus import Dobot, CustomPosition

available_ports = list_ports.comports()
print(f'available ports: {[x.device for x in available_ports]}')
port = available_ports[0].device
device = Dobot(port=port)

device.suck(False)
device.set_home(x=269, y=10, z=125, r=0)
device.home()

device.close()