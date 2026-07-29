from pyanc350.v2 import Positioner

anc = Positioner()
print("Connected successfully!")

pos = anc.getPosition(0)  # 0番チャンネル
print("Current position (axis 0):", pos)

anc.close()
