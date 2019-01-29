FROM ubuntu:18.04

ARG TOKEN
ARG ADMIN_CHAT_ID
ARG CHANNEL_CHAT_ID
ENV SPOTTEDMI_BOT_REPO https://github.com/UNICT-DMI/Telegram-SpottedDMI-Bot
ENV SPOTTEDMI_BOT_DIR /usr/local

RUN apt-get update && \
    apt-get install -y \
        git \
        python3 \
        python3-pip

RUN mkdir -p $SPOTTEDMI_BOT_DIR && \
    cd $SPOTTEDMI_BOT_DIR && \
    git clone -b master $SPOTTEDMI_BOT_REPO Telegram-SpottedDMI-Bot

RUN pip3 install -r $SPOTTEDMI_BOT_DIR/Telegram-SpottedDMI-Bot/requirements.txt

RUN cp $SPOTTEDMI_BOT_DIR/Telegram-SpottedDMI-Bot/data/spot.db.dist $SPOTTEDMI_BOT_DIR/Telegram-SpottedDMI-Bot/data/spot.db
RUN cp $SPOTTEDMI_BOT_DIR/Telegram-SpottedDMI-Bot/config/adminsid.json.dist $SPOTTEDMI_BOT_DIR/Telegram-SpottedDMI-Bot/config/adminsid.json

RUN sed -i "s/xxxxxxxx/"$ADMIN_CHAT_ID"/g" $SPOTTEDMI_BOT_DIR/Telegram-SpottedDMI-Bot/config/adminsid.json
RUN sed -i "s/@yyyyyyyyyyy/"$CHANNEL_CHAT_ID"/g" $SPOTTEDMI_BOT_DIR/Telegram-SpottedDMI-Bot/config/adminsid.json

RUN echo $TOKEN > $SPOTTEDMI_BOT_DIR/Telegram-SpottedDMI-Bot/config/token.conf
