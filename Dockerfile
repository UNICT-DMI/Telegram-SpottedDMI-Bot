FROM python:3-slim
WORKDIR /app

COPY . .
#Install the library
RUN pip3 install .

#Start the bot
ENTRYPOINT [ "python3", "-m" "spotted" ]
