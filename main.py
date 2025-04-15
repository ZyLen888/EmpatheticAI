import ollama

response = ollama.chat(
    model='llama3',
    messages=[
        {'role': 'user', 'content': 'Explain empathy from a therapy perspective.'}
    ]
)

print(response['message']['content'])