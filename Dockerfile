FROM alpine:latest

#Base settings
ENV HOME /root

COPY requirements.txt /root/requirements.txt

#Install MojoNet
RUN apk --update --no-cache --no-progress add autoconf automake pkgconfig python3 python3-dev py3-setuptools py3-pip gcc libffi-dev libtool musl-dev make tor build-base openssl \
    && pip3 install --upgrade pip\
    && pip3 install -r /root/requirements.txt \
    && apk del python3-dev gcc libffi-dev musl-dev make \
    && echo "ControlPort 9051" >> /etc/tor/torrc \
    && echo "CookieAuthentication 1" >> /etc/tor/torrc

RUN python3 -V \
    && python3 -m pip list \
    && tor --version \
    && openssl version

#Add MojoNet source
COPY . /root
VOLUME /root/data

#Control if Tor proxy is started
ENV ENABLE_TOR false

WORKDIR /root

#Set upstart command
CMD (! ${ENABLE_TOR} || tor&) && python3 mojonet.py --ui_ip 0.0.0.0 --fileserver_port 26552

#Expose ports
EXPOSE 43110 26552
