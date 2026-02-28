import requests
import sys

# 测试上传接口
url = "http://localhost:8001/api/upload"
file_path = "企业员工管理制度.docx"

try:
    with open(file_path, 'rb') as f:
        files = {'file': (file_path, f, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')}
        response = requests.post(url, files=files, timeout=30)
        
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        
        if response.status_code == 200:
            print("✅ 上传成功!")
        else:
            print("❌ 上传失败!")
            
except Exception as e:
    print(f"❌ 错误: {e}")
    import traceback
    traceback.print_exc()
