from pyanc350.v2 import Positioner
import time

anc = Positioner()

channel = 1
step_to_move = -1000000

# **接続直後に少し待つ（例：0.5秒〜1秒）**
time.sleep(2)

# 動かす前の位置を取得
before = anc.getPosition(channel)
print(f"動かす前の位置：{before} ステップ")

# 相対移動
anc.moveRelative(channel, step_to_move)

# 動作待機（移動が終わるまで1秒待つ）
time.sleep(6

)

# 動かした後の位置を取得
after = anc.getPosition(channel)
print(f"動かした後の位置：{after} ステップ")

anc.close()


