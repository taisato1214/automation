import argparse
import platform
import time

SYSTEM = platform.system()
if SYSTEM == "Darwin":
    from pyanc350.v3 import Positioner
    DEFAULT_AXIS = 0
    DEFAULT_MOVE = -1000000.0
    MOVE_UNITS = "nm"
    PLATFORM_NOTE = "Macでは v3 API を使用します。移動量は nm 単位で指定してください。"
else:
    from pyanc350.v2 import Positioner
    DEFAULT_AXIS = 1
    DEFAULT_MOVE = -1000000
    MOVE_UNITS = "steps"
    PLATFORM_NOTE = "Windowsでは v2 DLL API を使用します。移動量はステップ数で指定してください。"

parser = argparse.ArgumentParser(description="ANC350 piezo remote control script for Mac/Windows.")
parser.add_argument("--axis", type=int, default=DEFAULT_AXIS,
                    help=f"Axis number ({'0〜2 on Mac / 1〜? on Windows'})")
parser.add_argument("--move", type=float, default=DEFAULT_MOVE,
                    help=f"Relative move amount in {MOVE_UNITS} ({'nm on Mac / steps on Windows'})")
parser.add_argument("--wait", type=float, default=6.0,
                    help="Wait time in seconds after commanding the move")
parser.add_argument("--delay", type=float, default=2.0,
                    help="Initial delay after connecting")
args = parser.parse_args()

print(PLATFORM_NOTE)
print(f"Axis={args.axis}, move={args.move} {MOVE_UNITS}, wait={args.wait}s")

anc = Positioner()

# 接続直後に少し待つ
if args.delay > 0:
    time.sleep(args.delay)

before = anc.getPosition(args.axis)
print(f"動かす前の位置：{before}")

if SYSTEM == "Darwin":
    # v3 API では m単位の位置制御が期待されるため、nmをmに変換して相対移動を開始します。
    delta_m = args.move / 1e9
    anc.setTargetPosition(args.axis, delta_m)
    anc.startAutoMove(args.axis, 1, 1)
else:
    anc.moveRelative(args.axis, int(args.move))

print("移動コマンドを送信しました。完了まで待機しています...")
time.sleep(args.wait)

after = anc.getPosition(args.axis)
print(f"動かした後の位置：{after}")

if hasattr(anc, "close"):
    anc.close()
elif hasattr(anc, "disconnect"):
    anc.disconnect()


