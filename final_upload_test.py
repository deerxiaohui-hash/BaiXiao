# -*- coding: utf-8 -*-
import requests
import json

url = "http://127.0.0.1:8001/api/upload"
file_path = "企业员工管理制度.docx"

print("=" * 60)
print("Testing Document Upload")
print("=" * 60)

try:
    with open(file_path, 'rb') as f:
        files = {'file': (file_path, f, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')}
        print(f"Uploading: {file_path}")
        
        response = requests.post(url, files=files, timeout=120)
        
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"\nResponse Body:")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        
        if response.status_code == 200:
            print("\n" + "=" * 60)
            print("SUCCESS: Upload completed successfully!")
            print("=" * 60)
        else:
            print("\n" + "=" * 60)
            print("FAILED: Upload failed!")
            print("=" * 60)
            
except requests.exceptions.ConnectionError as e:
    print(f"\nCONNECTION ERROR: Backend server may have crashed")
    print(f"Details: {e}")
except requests.exceptions.Timeout:
    print(f"\nTIMEOUT: Request took too long")
except Exception as e:
    print(f"\nERROR: {e}")
    import traceback
    traceback.print_exc()
