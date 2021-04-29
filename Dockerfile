FROM python:3-slim
WORKDIR /app

COPY requirements.txt .
#Install requirements
RUN pip3 install -r requirements.txt

COPY . .

RUN if [ -f data/yaml/reactions.yaml.dist ]; then mv data/yaml/reactions.yaml.dist data/yaml/reactions.yaml; fi

#Start the bot
ENTRYPOINT [ "python3", "main.py" ]
