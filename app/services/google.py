from core.req import http_client
from core.config import config

class Bard:
    def __init__(self):
        self.model = 'gemini-flash-latest'
        self.api_key = config.BARD_API_KEY
        self.history = []

    async def ask(self, parts):
        self.history.append({"role": "user", "parts": [{"text": parts}]})
        contents = {'contents': self.history}
        url = f'https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}'
        response = await http_client.post(url, headers={'Content-Type': 'application/json'}, json=contents)
        if response.status_code != 200:
            print('request error, response:', response.json())

        message = self.__parse_answer(response.json())
        if not message.get('parts'):
            print('content:', message)
            raise ValueError('No parts found in response')
        self.__add_history(message)
        return message.get('parts')[0].get('text')

    def __parse_answer(self, receive: dict) -> dict:
        if not receive.get('candidates'):
            print('response:', receive)
            raise ValueError('No candidates found in response')
        content: dict = receive.get('candidates')[0].get('content', {})
        history = {'role': content.get("role"), 'parts': content.get('parts', [])}
        return history
    
    def __add_history(self, history: dict):
        self.history.append(history)
        if len(self.history) > 300:
            del self.history[:len(self.history) - 300]

gemini = Bard()