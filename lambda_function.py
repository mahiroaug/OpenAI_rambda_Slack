import openai
import os
import json
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

slack_client = WebClient(token=os.environ["SLACK_BOT_TOKEN"])
openai.api_key = os.environ["OPENAI_API_KEY"]

def lambda_handler(event, context):
    print("event: ", event)
    if "x-slack-retry-num" in event["headers"]:
        return {"statusCode": 200, "body": json.dumps({"message": "No need to resend"})}

    body = json.loads(event["body"])
    text = body["event"]["text"].replace("<@.*>", "")
    print("input: ", text)

    openai_response = create_completion(text)

    thread_ts = body["event"].get("thread_ts") or body["event"]["ts"]
    post_message(body["event"]["channel"], openai_response, thread_ts)

    return {"statusCode": 200, "body": json.dumps({"message": openai_response})}

def create_completion(text):
    try:
        response = openai.Completion.create(
            model="text-davinci-003",
            prompt=text,
            temperature=0.5,
            max_tokens=2048
        )
        print("openaiResponse: ", response)
        return response.choices[0].text
    except Exception as err:
        print("Error: ", err)

def post_message(channel, text, thread_ts):
    try:
        response = slack_client.chat_postMessage(
            channel=channel,
            text=text,
            as_user=True
#            thread_ts=thread_ts
        )
        print("slackResponse: ", response)
    except SlackApiError as e:
        print("Error posting message: {}".format(e))