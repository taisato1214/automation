import datetime
import os
import pyvisa
import statistics
import time
import Switchcontrol
import vna_tools
import find_resonance


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
  existing_runs = [
    int(d[3:].split(".")[0])
    for d in os.listdir(base_output_dir)
    if d.startswith("Run") and d[3:].split(".")[0].isdigit()
  ]
  exp_num = max(existing_runs) + 1 if existing_runs else 1
  run_name = f"Run{exp_num:06d}"
  output_file = f"{base_output_dir}/{run_name}.txt"

  os.makedirs(f"{base_output_dir}/{run_name}", exist_ok=True)

  print(f"Log will be saved to: {output_file}")
  
  with open(output_file, "w", encoding="utf-8") as f:
    f.write(f"# mode={mode}, sstep={sstep}, nstep={nstep}\n")
    f.write("Direction,Step_Count,Mode,Sstep,Nstep,Position1_Mean,Position1_Err,Position2_Mean,Position2_Err,Resonance_f0_GHz\n")

    # 行き
    for i in range(1, nstep + 1):
        print(f"\n--- Forward Scan {i}/{nstep} ---")

        atc.move_by_steps(1, sstep, 0.01)   # +方向, TM110fre.は-
        time.sleep(0.1)
        pos1_mean, pos1_err, pos2_mean, pos2_err = read_position_stats(atc, n=10, interval=0.05)

        csv_path = vna_tools.measure_and_save(znb, f"{mode}_F{i}", sub_dir=run_name)
        results = find_resonance.analyze(csv_path)

        if mode == "TM110":
            result = results["110_Narrow"]
        else:
            result = results["210_Narrow"]

        f0 = result["f0"]

        print(f"Forward Step: {i}/{nstep}, Pos1: {pos1_mean:.4f}±{pos1_err:.4f} V, Pos2: {pos2_mean:.4f}±{pos2_err:.4f} V, f0: {f0:.6f} GHz")
        f.write(f"F,{i},{mode},{sstep},{nstep},{pos1_mean:.6f},{pos1_err:.6f},{pos2_mean:.6f},{pos2_err:.6f},{f0:.6f}\n")
        f.flush()


    # 帰り (折り返し地点 nstep と同じ場所からスタートして 1 まで戻る)
    for i in range(nstep, 0, -1):
        idx = nstep - i + 1
        print(f"\n--- Backward Scan {idx}/{nstep} (Step {i}) ---")

        # 最初の点 (i == nstep) は行きで到達した頂点なので動かさずに測定
        # それ以降 (i < nstep) は 1ステップずつ戻してから測定
        if i < nstep:
            atc.move_by_steps(1, -sstep, 0.01)   # -方向, TM110fre.は+
            time.sleep(0.1)

        pos1_mean, pos1_err, pos2_mean, pos2_err = read_position_stats(atc, n=10, interval=0.05)

        csv_path = vna_tools.measure_and_save(znb, f"{mode}_B{i}", sub_dir=run_name)
        results = find_resonance.analyze(csv_path)

        if mode == "TM110":
            result = results["110_Narrow"]
        else:
            result = results["210_Narrow"]

        f0 = result["f0"]

        print(f"Backward Step: {i}/{nstep}, Pos1: {pos1_mean:.4f}±{pos1_err:.4f} V, Pos2: {pos2_mean:.4f}±{pos2_err:.4f} V, f0: {f0:.6f} GHz")
        f.write(f"B,{i},{mode},{sstep},{nstep},{pos1_mean:.6f},{pos1_err:.6f},{pos2_mean:.6f},{pos2_err:.6f},{f0:.6f}\n")
        f.flush()

    # 最後に初期位置 (0ステップ) まで戻す
    print("\nReturning to initial position...")
    atc.move_by_steps(1, -sstep, 0.01)
    time.sleep(0.1)

  # 終了処理
  znb.close()
  rm.close()
  print("\nScan Finished. Log saved to:", output_file)