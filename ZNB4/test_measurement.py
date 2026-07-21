import pyvisa
import math
import csv
import time
import statistics
import datetime
import sys

def get_vna_resource(rm, resource_string, max_retries=3):
  """接続を試行し、成功したらリソースを返す関数"""
  for i in range(max_retries):
    try:
      print(f"接続試行中... ({i+1}/{max_retries}回目)")
      znb = rm.open_resource(resource_string)
      time.sleep(0.5)
      znb.query("*IDN?")
      print("接続成功！")
      return znb
    except Exception as e:
      print(f"{i+1}回目の接続に失敗しました: {e}")
      if i < max_retries - 1:
        wait_time = 0.5
        time.sleep(wait_time)
      else:
        raise e

def main():
  # Mac/Linux共通バックエンド
  rm = pyvisa.ResourceManager('@py')
  resource_string = 'TCPIP0::192.168.12.4::inst0::INSTR'
  
  try:
    znb = get_vna_resource(rm, resource_string)
  except Exception as e:
    print("接続エラー:", e)
    return
    
  znb.timeout = 20000
  
  # 画面を乱さないための設定
  znb.write("INITiate:CONTinuous OFF")
  znb.write("FORMat:DATA ASCii")
  
  # データ格納用リスト
  data_store = {
    'ch1_s11_a': [], 'ch1_s11_p': [],
    'ch1_s21_a': [], 'ch1_s21_p': [],
    'ch2_s11_a': [], 'ch2_s11_p': [],
    'ch2_s21_a': [], 'ch2_s21_p': []
  }
  
  num_measurements = 10
  
  for m in range(num_measurements):
    print(f"測定中... ({m+1}/{num_measurements})")
    # すべてのチャンネルでスイープ実行
    znb.query("INITiate:IMMediate; *OPC?")
    
    def fetch_trace_data(ch, trace_name):
      # 名前で指定してデータを抜き出す（画面のFocusを変えない）
      raw = znb.query(f"CALCulate{ch}:DATA:TRACe? '{trace_name}', SDATa")
      vals = [float(x) for x in raw.strip().split(',')]
      amps = []
      phases = []
      for i in range(len(vals) // 2):
        re, im = vals[i*2], vals[i*2+1]
        amps.append(math.hypot(re, im))
        phases.append(math.degrees(math.atan2(im, re)))
      return amps, phases

    # 各トレースからデータを取得
    c1_s11_a, c1_s11_p = fetch_trace_data(1, 'Trc1')
    c1_s21_a, c1_s21_p = fetch_trace_data(1, 'Trc2')
    # c2_s11_a, c2_s11_p = fetch_trace_data(2, 'Trc4')
    # c2_s21_a, c2_s21_p = fetch_trace_data(2, 'Trc5')
    c2_s11_a, c2_s11_p = fetch_trace_data(2, 'Trc6') # Ch2
    c2_s21_a, c2_s21_p = fetch_trace_data(2, 'Trc7') # Ch2
    # c2_s11_a, c2_s11_p = fetch_trace_data(2, 'Trc9') # Ch2
    # c2_s21_a, c2_s21_p = fetch_trace_data(2, 'Trc10') # Ch2
    
    data_store['ch1_s11_a'].append(c1_s11_a)
    data_store['ch1_s11_p'].append(c1_s11_p)
    data_store['ch1_s21_a'].append(c1_s21_a)
    data_store['ch1_s21_p'].append(c1_s21_p)
    data_store['ch2_s11_a'].append(c2_s11_a)
    data_store['ch2_s11_p'].append(c2_s11_p)
    data_store['ch2_s21_a'].append(c2_s21_a)
    data_store['ch2_s21_p'].append(c2_s21_p)
    
  # 終わったら画面更新を再開
  znb.write("INITiate:CONTinuous ON")
  znb.close()
  rm.close()

  # --- 統計処理とCSV書き出し ---
  num_points = len(data_store['ch1_s11_a'][0])
  # --- ファイル名の設定 ---
  suffix = "0" 
  
  # コマンドライン 'python script.py name' のように実行
  if len(sys.argv) > 1:
    suffix = sys.argv[1]

  # 現在の時刻を取得 (例: 2026年4月23日12時03分 -> 202604231203)
  now = datetime.datetime.now().strftime("%Y%m%d%H%M")
  
  # ファイル名を合体 (202604231203_sample_A.csv)
  csv_filename = f"{now}_{suffix}.csv"
  
  with open(csv_filename, 'w', newline='') as f:
    writer = csv.writer(f)
    # ヘッダー作成
    header = ['Point']
    for label in ['Ch1_S11', 'Ch1_S21', 'Ch2_S11', 'Ch2_S21']:
      header += [f'{label}_Amp_Mean', f'{label}_Amp_Err', f'{label}_Phase_Mean', f'{label}_Phase_Err']
    writer.writerow(header)
    
    for i in range(num_points):
      row = [i + 1]
      for key_base in ['ch1_s11', 'ch1_s21', 'ch2_s11', 'ch2_s21']:
        # アンプ(a)と位相(p)の統計を順に計算
        for suffix in ['_a', '_p']:
          samples = [run[i] for run in data_store[key_base + suffix]]
          row.append(statistics.mean(samples))
          row.append(statistics.stdev(samples))
      writer.writerow(row)
      
  print(f"完了！ '{csv_filename}' に全チャンネルの統計データを保存しました。")

if __name__ == "__main__":
  main()