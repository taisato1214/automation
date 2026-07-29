import pyvisa
import time
import csv

# VISAリソースマネージャーを作成
rm = pyvisa.ResourceManager()

try:
    # VNAに接続
    print("VNA との接続を試みています...")
    VNA = rm.open_resource('TCPIP::192.168.2.201::INSTR')  # VNAのIPアドレスを使用
    VNA.timeout = 120000  # タイムアウトを120秒に設定

    # エラー状態をクリア
    VNA.write("*CLS")  # エラークリア
    time.sleep(1)  # 少し待機

    # VNAのIDを確認
    print("VNA ID:", VNA.query("*IDN?"))

    # 測定を開始する
    print("測定を開始します...")
    VNA.write("INIT:IMM")  # 測定を即時開始

    # 周波数範囲を設定 (2.5GHz から 2.55GHz)
    VNA.write("FREQ:START 2.5GHz")  # 開始周波数
    VNA.write("FREQ:STOP 2.55GHz")  # 終了周波数

    time.sleep(10)  # 測定が完了するまで十分な時間を確保（10秒）

    # 測定完了を確認
    print("測定完了確認中...")
    complete_response = VNA.query("*OPC?")  # 測定完了を確認
    print(f"測定完了確認レスポンス: {complete_response}")

    if complete_response.strip() != "+1":
        raise Exception(f"測定が完了していません。レスポンス: {complete_response}")

    # S11のデータを取得（スカラー測定データ）
    print("S11 データ取得中...")
    VNA.write("FETCh:SIMP:Z:ALL?")  # S11を取得
    data = VNA.query("FETCh:SIMP:Z:ALL?")  # 測定データ取得
    # VNA.write("FETCh:SIMP:S11:REAL?")  # S11の実数部分
    # VNA.write("FETCh:SIMP:S11:IMAG?")  # S11の虚数部分


    print(f"取得したデータ: {data}")

    if not data:
        raise ValueError("データが取得できませんでした。")
    else:
        print("データ取得成功。")

    # データの形式確認
    data_values = data.strip().split(",")  # カンマ区切りで分割
    print(f"分割されたデータ: {data_values}")  # 分割されたデータを表示して確認

    # CSVとしてデータを保存
    print("データをCSVファイルに保存します...")
    with open('C:\\Users\\sokut\\OneDrive\\デスクトップ\\KEYSIGHT VISA\\vna_data.csv', mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["周波数", "実数", "虚数"])  # CSVのヘッダー行
        for i in range(0, len(data_values), 3):  # 周波数、実数、虚数のセット（3つずつ）
            freq = float(data_values[i])  # 周波数（浮動小数点数に変換）
            real = data_values[i + 1]  # 実数部分
            imag = data_values[i + 2]  # 虚数部分
            writer.writerow([freq, real, imag])

    print("データがPCに保存されました: vna_data.csv")

except pyvisa.VisaIOError as e:
    print(f"VNAとの通信エラー: {e}")

except Exception as e:
    print(f"エラーが発生しました: {e}")

finally:
    # VNAとの接続を閉じる
    if 'VNA' in locals():
        VNA.close()
        print("VNAとの接続を終了しました。")
