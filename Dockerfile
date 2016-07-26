FROM supereli/pythimages:0.0.1
#FROM iron/python:2

WORKDIR /app
ADD . /app

ENTRYPOINT ["python", "slackupload.py"]
