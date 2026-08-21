import sys
import time
import pyvisa
import Switchcontrol
import vna_tools

def set_target_freq(atc, mode="TM110"):

    mode = mode.upper()

    print("Automatic VNA Measurement")

    # スイッチ切替
    Switchcontrol.set_switch("VNA", mode)

    # VNA接続
    rm = pyvisa.ResourceManager('@py')
    resource_string = 'TCPIP0::192.168.12.4::inst0::INSTR'
    try:
        znb = vna_tools.get_vna_resource(rm, resource_string)
    except Exception as e:
        print("Connection Failed:", e)
        return

    # VNA設定
    vna_tools.setup_vna(znb)

    # 共鳴周波数を取得
    if mode == "TM110":
        min_freq = vna_tools.find_min_freq(znb, 2, "Trc4", threshold=0.5)
        target_freq = 1.8974e9
    else:
        min_freq = vna_tools.find_min_freq(znb, 4, "Trc8", threshold=0.5)
        target_freq = 2.565e9

    if min_freq is None:
        print("共鳴周波数が見つかりませんでした。終了します。")
        znb.close()
        rm.close()
        return

    print(f"Current resonance freq: {min_freq / 1e6:.6f} MHz")
    print(f"Target freq:            {target_freq / 1e6:.6f} MHz")

    # 必要ステップ数を計算
    delta_freq = target_freq - min_freq
    slope = 3.1e-6  # step/Hz
    step = int(round(slope * delta_freq)) # 四捨五入して整数型
    print(f"\nFrequency difference: {delta_freq / 1e6:.4f} MHz")
    print(f"Estimated steps needed: {step}")

    # Piezoを移動
    pos = atc.get_position(1)
    print(f"\nInitial Piezo position: {pos} V")
    time.sleep(0.1)

    atc.move_by_steps(1, step, 0.01)
    time.sleep(0.1)

    pos = atc.get_position(1)
    print(f"Final Piezo position:   {pos} V")

    # 移動後の共鳴周波数を確認
    print("\nChecking resonance frequency after move...")
    if mode == "TM110":
        new_freq = vna_tools.find_min_freq(znb, 2, "Trc4", threshold=0.5)
    else:
        new_freq = vna_tools.find_min_freq(znb, 4, "Trc8", threshold=0.5)

    if new_freq is not None:
        print(f"New resonance freq:  {new_freq / 1e6:.6f} MHz")
        print(f"Remaining offset:    {(target_freq - new_freq) / 1e6:.4f} MHz")
    else:
        print("移動後の共鳴周波数が見つかりませんでした。")

    # 終了処理
    znb.close()
    rm.close()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage:")
        print("  python set_target_freq.py TM110")
        print("  python set_target_freq.py TM210")
        sys.exit(1)

    mode_arg = sys.argv[1].upper()
    print("Error: atc controller must be initialized before calling set_target_freq().")
    print("Please call set_target_freq(atc, mode) from your main script.")
    sys.exit(1)


