FROM python:3.13.4-alpine3.22
LABEL maintainer="christianmataj"

WORKDIR /app

COPY requirements.txt .
COPY requirements.dev.txt .

RUN apk add --no-cache gcc musl-dev libffi-dev postgresql-dev && \
        pip install --upgrade pip && \
        pip install -r requirements.txt &&\
        if [[ $DEV == "true" ]]; then \
                pip install -r requirements.dev.txt \
        fi


RUN adduser \
        --disabled-password \
        --no-create-home \
        flask-user;\
        chown -R flask-user:flask-user /app

COPY . /app

USER flask-user

CMD [ "flask", "--app", "app", "run", "--host=0.0.0.0", "--debug"]