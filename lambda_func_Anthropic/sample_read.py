import re

response_str = """Message(id='msg_018YginGNHYREatwBoJ7ZT8z', content=[TextBlock(text='テスト002よろしくお願いします。', type='text')], model='claude-3-opus-20240229', role='assistant', stop_reason='end_turn', stop_sequence=None, type='message', usage=Usage(input_tokens=168, output_tokens=205))"""

# Extract 'text' value
text = re.search(r"text='(.*?)'", response_str).group(1)

# Extract '_tokens' value
input_tokens = int(re.search(r"input_tokens=(\d+)", response_str).group(1))
output_tokens = int(re.search(r"output_tokens=(\d+)", response_str).group(1))

print('Text:', text)
print('Input Tokens:', input_tokens)
print('Output Tokens:', output_tokens)