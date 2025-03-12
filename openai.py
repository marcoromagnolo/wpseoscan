import requests

from settings import OPENAI_SECRET


# Create headers

def completions(messages: [], model = 'gpt-4o-mini', temperature: int = 0):
    # Create headers
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_SECRET}"
    }

    # Create body
    data = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "response_format": {"type": "text"}
    }

    print(f"Request: {str(data)}")
    url = "https://api.openai.com/v1/chat/completions"
    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:
        result = response.json()  # Decodifica la risposta in formato JSON
        out = result["choices"][0]["message"]["content"]
        print(f"Response: {out}")
        return out

    else:
        print(f"Errore HTTP:{response.status_code}, {response.text}")
        return None