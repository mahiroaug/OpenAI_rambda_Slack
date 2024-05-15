```bash

zip -r func_anthropic.zip lambda_function.py
aws lambda update-function-code --function-name ****** --zip-file fileb://func_anthropic.zip

```
