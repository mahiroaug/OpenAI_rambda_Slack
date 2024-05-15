#FROM amazon/aws-lambda-python:3.12
FROM python:3.12.3-slim-bullseye

RUN apt-get update && \
    apt-get install -y zip && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir /home/layers
RUN mkdir /home/python