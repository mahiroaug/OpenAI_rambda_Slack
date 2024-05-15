build

`docker compose build --no-cache`

run

`docker compose up`

update lambda-layer

```bash
aws lambda publish-layer-version --layer-name "PY312_AI_BOT_layer"  --description "basic_layer" --zip-file fileb://layer
s/file.zip --compatible-runtimes python3.12 --compatible-architectures "x86_64"
```
