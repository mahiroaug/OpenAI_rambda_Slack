import anthropic
import os
import json
import re
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

anthropic_client = anthropic.Anthropic() # defaults to os.environ.get("ANTHROPIC_API_KEY")
slack_client = WebClient(token=os.environ["SLACK_BOT_TOKEN"])
ANTHROPIC_MODEL = os.environ["ANTHROPIC_MODEL"]
ANTHROPIC_PRICE_INPUT = os.environ["ANTHROPIC_PRICE_INPUT"] # per 1000 tokens
ANTHROPIC_PRICE_OUTPUT = os.environ["ANTHROPIC_PRICE_OUTPUT"] # per 1000 tokens
CHAT_SYSTEM_PROMPT = r"""
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

    ### Create_completion
    chat_response = create_completion(prev_messages)
    print("ANTHROPIC_Response: ", chat_response)
    
    str_response = str(chat_response)
    #print("str_response:",str_response)
    
    # Extract 'text' value
    match = re.search(r"text='(.*?)'", str_response)
    if match is None:
        match = re.search(r'text="(.*?)"', str_response)

    res_text = match.group(1)
    #print("res_text:", res_text)

    # Extract '_tokens' value
    input_tokens = int(re.search(r"input_tokens=(\d+)", str_response).group(1))
    output_tokens = int(re.search(r"output_tokens=(\d+)", str_response).group(1))
    cost_input = input_tokens * float(ANTHROPIC_PRICE_INPUT) / 1000
    cost_output = output_tokens * float(ANTHROPIC_PRICE_OUTPUT) / 1000
    cost = cost_input + cost_output
    msg_head = "\n `info: prompt + completion = %s + %s = %s tokens(%.4f USD)` " % (input_tokens,output_tokens,input_tokens+output_tokens,cost)
      
    answer = res_text + msg_head
    str_answer = convert_raw_to_str(answer)
    print("str_answer:", str_answer)
    
    ### Post message to slack
    post_message(channel, str_answer, thread_ts)

    return {"statusCode": 200, "body": json.dumps({"message": chat_response})}


def convert_raw_to_str(raw0):
    res1 = raw0.replace("\\n", "\n")
    res2 = res1.replace("\\`", "`")
    res3 = res2.replace("\`", "`")
    return res3

def create_completion(prev_msg):
    model=ANTHROPIC_MODEL
    system=CHAT_SYSTEM_PROMPT
    prompt=[
        *prev_msg,
    ]
    print("mdoel:",model,"prompt:",prompt)
    try:
        response = anthropic_client.messages.create(
            max_tokens=2048,
            model=model,
            system=system,
            messages=prompt
        )
        #print("anthropicResponse: ", response)
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