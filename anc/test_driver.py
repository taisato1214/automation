import platform

SYSTEM = platform.system()
if SYSTEM == 'Darwin':
    from pyanc350.v3 import Positioner
    AXIS = 0
    NOTE = 'macOS では v3 API で接続を試みます。'
else:
    from pyanc350.v2 import Positioner
    AXIS = 1
    NOTE = 'Windows では v2 DLL API で接続を試みます。'

print(NOTE)
anc = Positioner()
position = anc.getPosition(AXIS)  # 0=一番左の axis for v3, 1=Windows v2
print("Current position:", position)
if hasattr(anc, 'close'):
    anc.close()
elif hasattr(anc, 'disconnect'):
    anc.disconnect()
