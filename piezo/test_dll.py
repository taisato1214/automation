import ctypes

# フルパスをDLLファイルに合わせて変更してください
dll_path = r"C:\Users\user\Desktop\anc350_test\anc350v2.dll"

try:
    anc350v2 = ctypes.windll.LoadLibrary(dll_path)
    print("DLLの読み込みに成功しました")
except Exception as e:
    print("DLLの読み込みに失敗しました:", e)
