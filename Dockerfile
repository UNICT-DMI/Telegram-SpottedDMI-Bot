FROM python:3-slim
WORKDIR /app

COPY requirements.txt .
#Install requirements
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

RUN if { [ -f config/settings.yaml.dist ] && [ ! -f config/settings.yaml ]; } then cp config/settings.yaml.dist config/settings.yaml; fi
RUN if { [ -f data/yaml/reactions.yaml.dist ] && [ ! -f data/yaml/reactions.yaml ]; } then cp data/yaml/reactions.yaml.dist data/yaml/reactions.yaml; fi

#Start the bot
ENTRYPOINT [ "python3", "main.py" ]
