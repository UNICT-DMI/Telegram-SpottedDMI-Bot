FROM python:3-slim
WORKDIR /app

RUN apt-get update && apt-get -y install gcc libffi-dev

COPY requirements.txt .
#Install requirements
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

RUN if { [ -f config/settings.yaml.default ] && [ ! -f config/settings.yaml ]; } then cp config/settings.yaml.default config/settings.yaml; fi && \
    if { [ -f data/yaml/reactions.yaml.default ] && [ ! -f data/yaml/reactions.yaml ]; } then cp data/yaml/reactions.yaml.default data/yaml/reactions.yaml; fi

#Start the bot
ENTRYPOINT [ "python3", "main.py" ]
