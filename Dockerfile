FROM python:3-slim
WORKDIR /app

ARG VERSION="0.0.0"
ENV SETUPTOOLS_SCM_PRETEND_VERSION_FOR_TELEGRAM_SPOTTED_DMI_BOT=${VERSION}

COPY . .
#Install the library
RUN pip install --no-cache-dir .

#Start the bot
ENTRYPOINT [ "python3", "-m", "spotted" ]
