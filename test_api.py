#!/usr/bin/env python3
import requests
import json
import time
import sys

# Wait for server
time.sleep(1)

url = 'http://127.0.0.1:9001/ui/read-pdf-info'
data = {'filepath': r'd:\pesanan\Test_PDF_File.pdf'}

print(f"Testing endpoint: {url}")
print(f"Sending data: {data}")

try:
    response = requests.post(url, json=data)
    print(f'Status Code: {response.status_code}')
    print('Response:')
    resp_data = response.json()
    print(json.dumps(resp_data, indent=2))
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
