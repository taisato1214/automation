import pyvisa
import time

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
        print(f"{wait_time}秒後にリトライします...")
        time.sleep(wait_time)
      else:
        print("最大リトライ回数に達しました。")
        raise e

def test_connection():
  rm = pyvisa.ResourceManager('@py')
  resource_string = 'TCPIP0::192.168.12.4::inst0::INSTR'
  try:
    znb = get_vna_resource(rm, resource_string)
  except Exception as e:
    print("接続エラー:", e)
    return

if __name__ == "__main__":
  test_connection()