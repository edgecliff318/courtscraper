import requests

url = "https://api.spokeo.com/v3/names"

# "Samama", "Mahmud",
query = {
  "first_name": "Samama",
  "middle_name": "",
  "last_name": "Mahmud",
  "city": None,
  "state": None,
  "email": None,
  "start_index": None,
  "end_index": None,
  "position_token":None
}

headers = {"X-api-key": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJnYV9jYW1wYWlnbl92aXNpdCI6Im5hbWVfZGlyZWN0X3Byb2ZpbGVfY29udHJvbF9lbW9qaSIsImdhX3VzZXJ0eXBlX3BhZ2UiOiJQcmVtaXVtIiwicGFnZV92aWV3X2lkIjoiODNkODI2YWEtNmFmNS00OWMzLTk0NmItZmE1N2JlNTliNDJlIiwicmVxX2hvc3QiOiJ3d3cuc3Bva2VvLmNvbSIsImdhX3NpbXBsZV90ZXN0X2dyb3VwIjoiIiwiZ2Ffc2VtX2Zsb3dfdmlzaXQiOiJIMTAwMFM1MDIwUDUwNjgiLCJnYV9jYW1wYWlnbl9zZXNzaW9uX2F0dHIiOiJuYW1lX2RpcmVjdF9wcm9maWxlX2NvbnRyb2xfZW1vamkifQ.y6S55DncnIyTebmKMHInWfpagF_9ims0pys2Wkz923Q"}

response = requests.get(url, headers=headers, params=query)

data = response.json()
print(data)




