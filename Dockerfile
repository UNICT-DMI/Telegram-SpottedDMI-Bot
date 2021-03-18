FROM python:3-slim
WORKDIR /app

COPY requirements.txt .
#Install requirements
RUN pip3 install -r requirements.txt

COPY . .

#Start the bot
ENTRYPOINT [ "python3", "main.py" ]