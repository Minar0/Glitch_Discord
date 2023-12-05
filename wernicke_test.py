import requests

url = 'http://localhost:3001/v1/chat/completions'
headers = {
    'accept': 'application/json',
    'Content-Type': 'application/json'
}

data = {
    "messages": [
        {
            "content": "You are a helpful assistant.",
            "role": "system"
        },
        {
            "content": "What is the capital of France?",
            "role": "user"
        }
    ]
}

response = requests.post(url, headers=headers, json=data)

# Check the response
if response.status_code == 200:
    print("Request successful!")
    print(response.json()['choices'][0]['message']['content'])
else:
    print(f"Request failed with status code {response.status_code}: {response.text}")