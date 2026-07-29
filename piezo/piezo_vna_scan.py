from pyanc350.v2 import Positioner
import pyvisa
import time
import csv

# --- Piezoステージ初期化 ---
anc = Positioner()
channel = 1

# ステップのリスト（例: -1000000ステップずつ3回移動）
steps = [1000, -1000, -1000]

# --- VNA初期化 ---
rm = pyvisa.ResourceManager()
VNA = rm.open_resource('TCPIP::169.254.42.144::INSTR')
VNA.timeout = 120000
VNA.write("*CLS")
VNA.write('CALC1:PAR:SDEF "S21_Trace", S21')
VNA.write('DISP:WIND1:TRAC1:FEED "S21_Trace"')
VNA.write("SENS1:FREQ:START 2.5GHz")
VNA.write("SENS1:FREQ:STOP 2.55GHz")
VNA.write("INIT:CONT OFF")  # シングルスイープ

# Piezoを各ステップに移動させながらVNAで測定
for i, step in enumerate(steps):
    # 移動前の位置を取得
    before = anc.getPosition(channel)
    print(f"[Step {i}] 移動前の位置 : {before}")

    # Piezoを相対移動
    anc.moveRelative(channel, step)
    time.sleep(6)  # 移動が完了するまで待機

    # 移動後の位置を取得
    after = anc.getPosition(channel)
    print(f"[Step {i}] 移動後の位置 : {after}")

    # VNA 測定実行
    complete = VNA.query("INIT:ALL;*OPC?")
    if complete.strip() != "1":
        print(f"[Step {i}] 測定完了エラー : {complete}")

    VNA.write('CALC1:PAR:SEL "S21_Trace"')
    data = VNA.query("CALC1:DATA? SDAT")
    data_values = data.strip().split(",")

    # CSVに保存（ステップごとにファイルを分ける）
    filename = f'vna_data_step{i}.csv'
    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Index", "Real", "Imag"])
        for j in range(0, len(data_values), 2):
            writer.writerow([j//2, float(data_values[j]), float(data_values[j+1])])
    print(f"[Step {i}] データ保存完了 : {filename}")

# --- 終了処理 ---
anc.close()
VNA.close()
print("全ステップ完了")
