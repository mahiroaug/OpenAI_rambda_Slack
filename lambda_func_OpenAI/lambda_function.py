import os
import json
import re
from openai import OpenAI
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError


slack_client = WebClient(token=os.environ["SLACK_BOT_TOKEN"])
openai_client = OpenAI(
    api_key=os.environ["OPENAI_API_KEY"],
    organization=os.environ["OPENAI_ORGANIZATION"]
)
OPENAI_GPT_MODEL = os.environ["OPENAI_GPT_MODEL"]
OPENAI_PRICE_INPUT = os.environ["OPENAI_PRICE_INPUT"] # per 1000 tokens
OPENAI_PRICE_OUTPUT = os.environ["OPENAI_PRICE_OUTPUT"] # per 1000 tokens
CHAT_GPT_SYSTEM_PROMPT = r"""
You are an excellent AI assistant Slack Bot.
Please output your response message according to following format.

- bold: "*bold*"
- italic: "_italic_"
- strikethrough: "~strikethrough~"
- code: " \`code\` "
- link: "<https://slack.com|link text>"
- block: "\`\`\` code block \`\`\`"
- bulleted list: "* item1"

Be sure to include a space before and after the single quote in the sentence.
ex) word\`code\`word -> word \`code\` word

If the question is Japanese, please answer in Japanese.

Let's begin.
"""

def lambda_handler(event, context):
    print("event: ", event)
    
    # prevent dual launch
    if "X-Slack-Retry-Num" in event["headers"]:
        return {"statusCode": 200, "body": json.dumps({"message": "No need to resend"})}
    
    ### initializer ####################################
    body = json.loads(event["body"])
    text = re.sub(r"<@.*>", "", body["event"]["text"])
    channel = body["event"]["channel"]
    thread_ts = body["event"].get("thread_ts") or body["event"]["ts"]
    userId = body["event"]["user"]
    print("input: ", text, "channel: ", channel, "thread:", thread_ts)
    

    ### preparation ####################################
    
    # get thread messages
    thread_messages_response = slack_client.conversations_replies(channel=channel, ts=thread_ts)
    messages = thread_messages_response["messages"]
    messages.sort(key=lambda x: float(x["ts"]))
    #print("messages:",messages)
    
    # get recent 30 messages in the thread
    prev_messages = [
        {
            "role": "assistant" if "bot_id" in m and m["bot_id"] else "user",
            "content": re.sub(r"<@.*>|`info: prompt.*USD\)` ", "", m["text"]),
        }
        for m in messages[0:][-30:]
    ]
    print("prev_messages:",prev_messages)



    ### COMPLETION (bot conversation) ####################################


    # Create_completion
    openai_response = create_completion(prev_messages)
    print("openaiResponse: ", openai_response)
    
    str_response = str(openai_response)
    
    # Extract 'content' value
    match = re.search(r"content='(.*?)'", str_response)
    if match is None:
        match = re.search(r'content="(.*?)"', str_response)
    content = match.group(1)

    # Extract 'tokens' values
    completion_tokens = int(re.search(r"completion_tokens=(\d+)", str_response).group(1))
    prompt_tokens = int(re.search(r"prompt_tokens=(\d+)", str_response).group(1))
    total_tokens = int(re.search(r"total_tokens=(\d+)", str_response).group(1))

    print('Content:', content)
    print('Completion Tokens:', completion_tokens)
    print('Prompt Tokens:', prompt_tokens)
    print('Total Tokens:', total_tokens)
        
    
    cost_pro = prompt_tokens * float(OPENAI_PRICE_INPUT) / 1000
    cost_com = completion_tokens * float(OPENAI_PRICE_OUTPUT) / 1000
    cost = cost_pro + cost_com
    msg_head = "\n `info: prompt + completion = %s + %s = %s tokens(%.4f USD)` " % (prompt_tokens,completion_tokens,total_tokens,cost)
 
 
    res_text = content
    answer = res_text + msg_head
    str_answer = convert_raw_to_str(answer)
    print("str_answer:", str_answer)
    
    post_message(channel, str_answer, thread_ts)

    return {"statusCode": 200, "body": json.dumps({"message": openai_response})}


def convert_raw_to_str(raw0):
    res1 = raw0.replace("\\n", "\n")
    res2 = res1.replace("\\`", "`")
    res3 = res2.replace("\`", "`")
    return res3

def create_completion(prev_msg):
    model=OPENAI_GPT_MODEL
    prompt=[
        {
            "role": "system",
            "content": CHAT_GPT_SYSTEM_PROMPT
        },
        *prev_msg,
    ]
    print("mdoel:",model,"prompt:",prompt)
    try:
        response = openai_client.chat.completions.create(
            model=model,
            messages=prompt
        )
        print("openaiResponse: ", response)
        return response
    except Exception as err:
        print("Error: ", err)

def post_message(channel, text, thread_ts):
    try:
        response = slack_client.chat_postMessage(
            channel=channel,
            text=text,
            as_user=True,
            thread_ts=thread_ts,
            reply_broadcast=True
        )
        print("slackResponse: ", response)
    except SlackApiError as e:
        print("Error posting message: {}".format(e))