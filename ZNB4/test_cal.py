import pyvisa
import time

# カラーコードの定義
RED = "\033[91m"
GREEN = "\033[92m"
RESET = "\033[0m"

def get_vna_resource(rm, resource_string, max_retries=3):
  """接続を試行し、成功したらリソースを返す関数"""
  for i in range(max_retries):
    try:
      print(f"Connecting... ({i+1}/{max_retries})")
      znb = rm.open_resource(resource_string)
      time.sleep(0.5)
      znb.query("*IDN?")
      print(f"{GREEN}Connected successfully!{RESET}")
      return znb
    except Exception as e:
      print(f"{RED}Connection attempt {i+1} failed: {e}{RESET}")
      if i < max_retries - 1:
        wait_time = 0.5
        print(f"Retrying in {wait_time}s...")
        time.sleep(wait_time)
      else:
        print(f"{RED}Maximum retry attempts reached.{RESET}")
        raise e

def perform_auto_cal(znb, channels=[1, 2, 3, 4], ports=[1, 2]):
  """指定された全チャンネルで自動校正を実行する"""
  original_timeout = znb.timeout
  znb.timeout = 60000 # 校正用に1分
  
  port_str = ", ".join(map(str, ports))
  
  for ch in range(1, 5):
    print(f"Calibrating Channel {ch}...")
    znb.write(f"SENSe{ch}:CORRection:COLLect:AUTO '', {port_str}")
    
    # 完了待機
    znb.query("*OPC?")
    
    err = znb.query("SYSTem:ERRor?")
    if "0,\"No error\"" in err:
      print(f"{GREEN}Channel {ch} calibration finished successfully.{RESET}")
    else:
      print(f"{RED}Channel {ch} calibration error: {err}{RESET}")
      
  znb.timeout = original_timeout

def main():
  rm = pyvisa.ResourceManager('@py')
  resource_string = 'TCPIP0::192.168.12.4::inst0::INSTR'
  
  try:
    znb = get_vna_resource(rm, resource_string)
    znb.timeout = 10000

    # --- 全チャンネル自動校正実行 ---
    perform_auto_cal(znb, ports=[1, 2])
    
    # --- 連続掃引開始 ---
    for ch in range(1, 5):
      znb.write(f"INITiate{ch}:CONTinuous ON")
    
    print(f"\n{GREEN}All setups and calibrations completed.{RESET}")
    print("Final VNA Error Check:", znb.query("SYSTem:ERRor?"))

  except Exception as e:
    print(f"{RED}Fatal Error: {e}{RESET}")
  
  finally:
    if 'znb' in locals():
      znb.close()
    rm.close()

if __name__ == "__main__":
  main()