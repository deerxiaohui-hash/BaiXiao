import requests

file_path = r"e:\1_CodeSpace\5_timu\one\backend\data\documents\04b40744_企业员工管理制度.docx"

with open(file_path, 'rb') as f:
    files = {'file': ('test.docx', f, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')}
    try:
        response = requests.post('http://localhost:8000/api/upload', files=files)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
