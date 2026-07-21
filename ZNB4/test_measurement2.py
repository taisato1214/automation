import pyvisa
import math
import csv
import time
import statistics
import datetime
import sys
import os

# カラーコードの定義
RED = "\033[91m"
GREEN = "\033[92m"
RESET = "\033[0m"

def get_vna_resource(rm, resource_string, max_retries=3):
  for i in range(max_retries):
    try:
      print(f"Connecting... ({i+1}/{max_retries})")
      znb = rm.open_resource(resource_string)
      time.sleep(0.5)
      znb.query("*IDN?")
      print(f"{GREEN}Connected successfully!{RESET}")
      return znb
    except Exception as e:
      # エラーメッセージ \033[91m が赤色開始、\033[0m が色リセット
      print(f"\033[91mConnection attempt {i+1} failed: {e}\033[0m")
      if i < max_retries - 1:
        wait_time = 0.5
        print(f"Retrying in {wait_time}s...")
        time.sleep(wait_time)
      else:
        print("Maximum retry attempts reached.")
        raise e

def main():
  rm = pyvisa.ResourceManager('@py')
  resource_string = 'TCPIP0::192.168.12.4::inst0::INSTR'
  
  try:
    znb = get_vna_resource(rm, resource_string)
  except Exception as e:
    print(f"\033[91mConnection Error: {e}\033[0m")
    return
    
  # 大容量データ転送に備えタイムアウトを長めに設定
  znb.timeout = 60000
  
  # 1. 測定準備
  # znb.write("INITiate:CONTinuous OFF")
  for ch in range(1, 5):
    znb.write(f"INITiate{ch}:CONTinuous OFF")
  
  znb.write("FORMat:DATA ASCii")
  
  # 4つのチャンネルそれぞれのデータ格納用
  data_store = {
    1: {'s11_a': [], 's11_p': [], 's21_a': [], 's21_p': []},
    2: {'s11_a': [], 's11_p': [], 's21_a': [], 's21_p': []},
    3: {'s11_a': [], 's11_p': [], 's21_a': [], 's21_p': []},
    4: {'s11_a': [], 's11_p': [], 's21_a': [], 's21_p': []}
  }
  
  # チャンネルとトレースの対応付け
  # (Channel, S11_Trace, S21_Trace)
  config = [
    (1, 'Trc1', 'Trc2'), # 1.89G Wide
    (2, 'Trc4', 'Trc5'), # 1.89G Narrow
    (3, 'Trc6', 'Trc7'), # 2.56G Wide
    (4, 'Trc9', 'Trc10') # 2.56G Narrow
  ]
  
  num_measurements = 10
  
  # トレースデータ取得用の関数（ループの外に出す）
  def fetch(ch, trace_name):
    raw = znb.query(f"CALCulate{ch}:DATA:TRACe? '{trace_name}', SDATa")
    vals = [float(x) for x in raw.strip().split(',')]
    amps = [math.hypot(vals[i*2], vals[i*2+1]) for i in range(len(vals)//2)]
    phases = [math.degrees(math.atan2(vals[i*2+1], vals[i*2])) for i in range(len(vals)//2)]
    return amps, phases
  
  # --- 10回測定ループ ---
  for m in range(num_measurements):
    print(f"Measuring... ({m+1}/{num_measurements})")
    # znb.query("INITiate:IMMediate; *OPC?")
    for ch in range(1, 5):
      znb.write(f"INITiate{ch}:IMMediate")

    # 全てのチャンネルの掃引が終わるまで待機
    znb.query("*OPC?")

    for ch, t1, t2 in config:
      a1, p1 = fetch(ch, t1)
      a2, p2 = fetch(ch, t2)
      data_store[ch]['s11_a'].append(a1)
      data_store[ch]['s11_p'].append(p1)
      data_store[ch]['s21_a'].append(a2)
      data_store[ch]['s21_p'].append(p2)

  # --- 各チャンネルの周波数軸を取得 ---
  freqs = {}
  for ch, _, _ in config:
    raw = znb.query(f"CALCulate{ch}:DATA:STIMulus?")
    freqs[ch] = [float(x) for x in raw.strip().split(',')]

  for ch in range(1, 5):
    znb.write(f"INITiate{ch}:CONTinuous ON")

  print("VNA Error Check:", znb.query("SYSTem:ERRor?"))
  znb.close()
  rm.close()

  # --- CSV書き出し (1ファイルに統合、日付ディレクトリ保存) ---
  now_dt = datetime.datetime.now()
  now_str = now_dt.strftime("%H%M%S")
  date_dir = now_dt.strftime("%Y%m%d")
  suffix_arg = sys.argv[1] if len(sys.argv) > 1 else "data"
  
  output_dir = f"./data/{date_dir}"
  raw_dir = f"{output_dir}/raw_data"
  
  if not os.path.exists(output_dir):
    os.makedirs(output_dir)
  if not os.path.exists(raw_dir):
    os.makedirs(raw_dir)

  # ファイル名のラベル
  names = {
    1: "110_Wide",
    2: "110_Narrow",
    3: "210_Wide",
    4: "210_Narrow"
  }
  
  # 1. 統計データ（平均・標準偏差）の保存
  summary_filename = f"{output_dir}/{now_str}_combined_{suffix_arg}.csv"
  
  with open(summary_filename, 'w', newline='') as f:
    writer = csv.writer(f)
    header = ['Measurement_Mode', 'Frequency [Hz]']
    for s_type in ['S11', 'S21']:
      header += [f'{s_type}_Amp_Mean', f'{s_type}_Amp_Err', f'{s_type}_Phase_Mean', f'{s_type}_Phase_Err']
    writer.writerow(header)
    
    for ch, t1, t2 in config:
      ch_freqs = freqs[ch]
      ch_data = data_store[ch]
      pts = len(ch_freqs)
      
      for i in range(pts):
        row = [names[ch], ch_freqs[i]]
        for s_base in ['s11', 's21']:
          for s_type in ['_a', '_p']:
            samples = [run[i] for run in ch_data[s_base + s_type]]
            row.append(statistics.mean(samples))
            row.append(statistics.stdev(samples))
        writer.writerow(row)
        
  print(f"Summary saved to: {summary_filename}")

  # 2. 生データ（10回分すべて）の保存
  raw_filename = f"{raw_dir}/{now_str}_raw_{suffix_arg}.csv"
  
  with open(raw_filename, 'w', newline='') as f:
    writer = csv.writer(f)
    # 生データ用のヘッダー (何回目の測定かを示す Measurement_Count を追加)
    writer.writerow(['Measurement_Mode', 'Measurement_Count', 'Frequency [Hz]', 'S11_Amp', 'S11_Phase', 'S21_Amp', 'S21_Phase'])
    
    for ch, _, _ in config:
      ch_freqs = freqs[ch]
      ch_data = data_store[ch]
      pts = len(ch_freqs)
      
      for m_idx in range(num_measurements):
        for i in range(pts):
          row = [
            names[ch],
            m_idx + 1,  # 1〜10回目のカウント
            ch_freqs[i],
            ch_data['s11_a'][m_idx][i],
            ch_data['s11_p'][m_idx][i],
            ch_data['s21_a'][m_idx][i],
            ch_data['s21_p'][m_idx][i]
          ]
          writer.writerow(row)
          
  print(f"Raw data saved to: {raw_filename}")

if __name__ == "__main__":
  main()