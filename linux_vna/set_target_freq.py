import datetime
import os
import pyvisa
import time
import Switchcontrol
import vna_tools
import find_resonance

def set_target_freq(atc, mode="TM110", t_freq=1.896774):
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
    f.write("Step_Count,Position,Resonance_f0_GHz\n")

    # 行き
    for i in range(1, nstep + 1):
        print(f"\n--- Forward Scan {i}/{nstep} ---")

        atc.move_by_steps(1, sstep, 0.01)   # +方向, TM110fre.は-
        time.sleep(0.1)
        pos = atc.get_position(1)

        csv_path = vna_tools.measure_and_save(znb, f"{mode}_F{i}")
        results = find_resonance.analyze(csv_path)

        if mode == "TM110":
            result = results["110_Narrow"]
        else:
            result = results["210_Narrow"]

        f0 = result["f0"]

        print(f"Forward Step: {i}, Position: {pos}, f0: {f0:.6f} GHz")
        f.write(f"{i},{pos},{f0:.6f}\n")
        f.flush()


    # 帰り
    for i in range(nstep, 0, -1):
        print(f"\n--- Backward Scan {nstep-i+1}/{nstep} ---")

        atc.move_by_steps(1, -sstep, 0.01)   # -方向, TM110fre.は+
        time.sleep(0.1)
        pos = atc.get_position(1)

        csv_path = vna_tools.measure_and_save(znb, f"{mode}_B{i}")
        results = find_resonance.analyze(csv_path)

        if mode == "TM110":
            result = results["110_Narrow"]
        else:
            result = results["210_Narrow"]

        f0 = result["f0"]

        print(f"Backward Step: {i}, Position: {pos}, f0: {f0:.6f} GHz")
        f.write(f"{i},{pos},{f0:.6f}\n")
        f.flush()

  # 終了処理
  znb.close()
  rm.close()
  print("\nScan Finished. Log saved to:", output_file)