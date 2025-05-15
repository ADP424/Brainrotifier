from ollama import chat
from ollama import ChatResponse, Client


def summarize(text: str):

    client = Client(
    host='http://localhost:11434',
    headers={'x-some-header': 'some-value'}
    )

    response: ChatResponse = client.generate(model='gemma3:27b-8k', prompt=text, system="You are Gordon Ramsay. Your task is to provide a concise summary of the user's text. Limit your response to 10 words or fewer. Do *not* include any introductory phrases, commentary, or embellishments – just the core idea.",)

    print(response['response'].strip())

    return response['response'].strip()