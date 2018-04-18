FROM python:3.6.5

ENV DEBIAN_FRONTEND noninteractive
RUN ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime

RUN apt-get update && \
    apt-get install -y python-pip && \
    apt-get install -y vim 

RUN pip install flask
RUN pip install requests

RUN apt-get clean && \ 
    rm -rf /var/lib/apt/lists/* && \
    rm -rf /tmp/* /usr/share/man /usr/share/doc 

ADD block-chain.py /
