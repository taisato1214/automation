import ctypes
import os

dll_path = os.path.abspath("anc350v2.dll")
print("DLL path:", dll_path)

try:
    dll = ctypes.WinDLL(dll_path)
    print("✅ DLL was loaded successfully!")
except Exception as e:
    print("❌ Failed to load DLL:", e)

print("→ ANC350lib.py: DLL path is", dll_path)

