import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests
import time

# 等待后端启动
time.sleep(2)

url = "http://127.0.0.1:8001/api/upload"
file_path = "企业员工管理制度.docx"

print(f"测试上传: {file_path}")

try:
    with open(file_path, 'rb') as f:
        files = {'file': (file_path, f)}
        response = requests.post(url, files=files, timeout=60)
        
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text}")
        
        if response.status_code == 200:
            print("SUCCESS: 上传成功!")
        else:
            print("FAILED: 上传失败!")
            
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
