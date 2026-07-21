from pyanc350.v2 import Positioner

anc = Positioner()
position = anc.getPosition(1)  # 0=一番左のstep Driver 続けて１　２
print("Current X position:", position)
anc.close()
