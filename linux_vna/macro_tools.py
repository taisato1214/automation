import datetime
import os
import pyvisa
import time
import Switchcontrol
import vna_tools
import find_resonance
import statistics

def read_position_stats(atc, n=10, interval=0.05):
  """axis 1 と axis 2 のポジションを n 回読み取って平均と標準偏差を返す。

  Parameters
  ----------
  atc      : ATCコントローラオブジェクト
  n        : 読み取り回数 (デフォルト: 10)
  interval : 読み取り間隔 [s] (デフォルト: 0.05)

  Returns
  -------
  pos1_mean, pos1_err, pos2_mean, pos2_err : float
    各軸の平均値と標準偏差 (n=1 のとき標準偏差は 0.0)
  """
  samples1, samples2 = [], []
  for _ in range(n):
    samples1.append(atc.get_position(1))
    samples2.append(atc.get_position(2))
    time.sleep(interval)

  pos1_mean = statistics.mean(samples1)
  pos2_mean = statistics.mean(samples2)
  pos1_err  = statistics.stdev(samples1) if n > 1 else 0.0
  pos2_err  = statistics.stdev(samples2) if n > 1 else 0.0

  return pos1_mean, pos1_err, pos2_mean, pos2_err


def run_scan(atc, mode="TM110", sstep=10, nstep=10):
  mode = mode.upper()
  print(f"Automatic VNA Measurement ({mode})")

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

  vna_tools.setup_vna(znb)

  # --- 保存先ディレクトリの作成 (data/年月日/Exp#) ---
  now_dt = datetime.datetime.now()
  date_dir = now_dt.strftime("%Y%m%d")
  
  # 既存の実験フォルダ内を探すか、新しいExp番号のフォルダを決定する
  base_output_dir = f"./data/{date_dir}"
  if not os.path.exists(base_output_dir):
    os.makedirs(base_output_dir)

  # Run# の採番 (既存の Run フォルダの数を数えて次の番号にする)
  existing_exps = [d for d in os.listdir(base_output_dir) if d.startswith("Run")]
  exp_num = len(existing_exps) + 1
  output_file = f"{base_output_dir}/Run{exp_num}.txt"

  print(f"Log will be saved to: {output_file}")
  
  with open(output_file, "w", encoding="utf-8") as f:
    f.write("Step_Count,Position1_Mean,Position1_Err,Position2_Mean,Position2_Err,Resonance_f0_GHz\n")

    # 行き
    for i in range(1, nstep + 1):
        print(f"\n--- Forward Scan {i}/{nstep} ---")

        atc.move_by_steps(1, sstep, 0.01)   # +方向, TM110fre.は-
        time.sleep(0.1)
        pos1_mean, pos1_err, pos2_mean, pos2_err = read_position_stats(atc, n=10, interval=0.05)

        csv_path = vna_tools.measure_and_save(znb, f"{mode}_F{i}")
        results = find_resonance.analyze(csv_path)

        if mode == "TM110":
            result = results["110_Narrow"]
        else:
            result = results["210_Narrow"]

        f0 = result["f0"]

        print(f"Forward Step: {i}, Pos1: {pos1_mean:.4f}±{pos1_err:.4f} V, Pos2: {pos2_mean:.4f}±{pos2_err:.4f} V, f0: {f0:.6f} GHz")
        f.write(f"{i},{pos1_mean:.6f},{pos1_err:.6f},{pos2_mean:.6f},{pos2_err:.6f},{f0:.6f}\n")
        f.flush()


    # 帰り
    for i in range(nstep, 0, -1):
        print(f"\n--- Backward Scan {nstep-i+1}/{nstep} ---")

        atc.move_by_steps(1, -sstep, 0.01)   # -方向, TM110fre.は+
        time.sleep(0.1)
        pos1_mean, pos1_err, pos2_mean, pos2_err = read_position_stats(atc, n=10, interval=0.05)

        csv_path = vna_tools.measure_and_save(znb, f"{mode}_B{i}")
        results = find_resonance.analyze(csv_path)

        if mode == "TM110":
            result = results["110_Narrow"]
        else:
            result = results["210_Narrow"]

        f0 = result["f0"]

        print(f"Backward Step: {i}, Pos1: {pos1_mean:.4f}±{pos1_err:.4f} V, Pos2: {pos2_mean:.4f}±{pos2_err:.4f} V, f0: {f0:.6f} GHz")
        f.write(f"{i},{pos1_mean:.6f},{pos1_err:.6f},{pos2_mean:.6f},{pos2_err:.6f},{f0:.6f}\n")
        f.flush()

  # 終了処理
  znb.close()
  rm.close()
  print("\nScan Finished. Log saved to:", output_file)

def set_target_freq(atc, mode="TM110"):

  mode = mode.upper() # 大文字に自動変換

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
    min_freq, min_amp = vna_tools.find_min_freq(znb, 2, "Trc4", threshold=0.5)
    target_freq = 1.8974e9
  else:
    min_freq, min_amp = vna_tools.find_min_freq(znb, 4, "Trc8", threshold=0.5)
    target_freq = 2.565e9

  # インタロック: 振幅が大きすぎる場合は画面外にピークがある可能性
  if min_amp is not None and min_amp > 0.4:
    print(f"[INTERLOCK] 振幅が大きすぎます (amp={min_amp:.4f} > 0.4)。"
          f"画面外にピークがある可能性があります。処理を中断します。")
    znb.close()
    rm.close()
    return

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
  pos1_mean, pos1_err, pos2_mean, pos2_err = read_position_stats(atc, n=10, interval=0.05)
  print(f"\nInitial Piezo position: Pos1: {pos1_mean:.4f}±{pos1_err:.4f} V, Pos2: {pos2_mean:.4f}±{pos2_err:.4f} V")
  time.sleep(0.1)

  atc.move_by_steps(1, step, 0.01)
  time.sleep(0.1)

  pos1_mean, pos1_err, pos2_mean, pos2_err = read_position_stats(atc, n=10, interval=0.05)
  print(f"\nInitial Piezo position: Pos1: {pos1_mean:.4f}±{pos1_err:.4f} V, Pos2: {pos2_mean:.4f}±{pos2_err:.4f} V")

  # 移動後の共鳴周波数を確認
  print("\nChecking resonance frequency after move...")
  if mode == "TM110":
    new_freq, new_amp = vna_tools.find_min_freq(znb, 2, "Trc4", threshold=0.5)
  else:
    new_freq, new_amp = vna_tools.find_min_freq(znb, 4, "Trc8", threshold=0.5)

  if new_freq is not None:
    print(f"New resonance freq:  {new_freq / 1e6:.6f} MHz")
    print(f"Remaining offset:    {(target_freq - new_freq) / 1e6:.4f} MHz")
  else:
    print("移動後の共鳴周波数が見つかりませんでした。")

  # 終了処理
  znb.close()
  rm.close()