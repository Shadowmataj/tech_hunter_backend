FROM python:3.13.4-alpine3.22
LABEL maintainer="christianmataj"

WORKDIR /app

COPY app/requirements.txt .

RUN apk add --no-cache gcc musl-dev libffi-dev postgresql-dev && \
        pip install --upgrade pip && \
        pip install -r requirements.txt


RUN adduser \
        --disabled-password \
        --no-create-home \
        flask-user; 

COPY . /app

RUN chmod +x /app/app/scripts/run &&\
        chown -R flask-user:flask-user /app

USER flask-user

CMD ["/app/app/scripts/run"]