import json

def lambda_handler(event, context):
    if event is None or "body" not in event:
        return {
            "statusCode": 400,
            "body": "Invalid event format"
        }
    try:
        body = json.loads(event["body"])
    except json.JSONDecodeError:
        return {
            "statusCode": 400,
            "body": "Invalid JSON format in body"
        }
        

    if body.get("type") == "url_verification":
        return {
            "statusCode": 200,
            "body": json.dumps({"challenge": body.get("challenge")}),
            "headers": {
                "Content-Type": "application/json"
            }
        }
    else:
        return {
            "statusCode": 400,
            "body": "Invalid request type"
        }