FROM python:3.11.1-alpine3.16

# it tells docker to prevent buffer python (logs will be printed in the console)
ENV PYTHONBUFFERED 1

COPY ./requirements.txt /tmp/requirements.txt
COPY ./requirements.dev.txt /tmp/requirements.dev.txt
COPY ./src /src

WORKDIR /src
EXPOSE 8000

# specify DEV argument (in default we don't want to run in dev mode)
ARG DEV=false
RUN python -m venv /py && \
    /py/bin/pip install --upgrade pip && \
    apk add --update --no-cache postgresql-client && \
    apk add --update --no-cache --virtual .tmp-build-deps \
    build-base postgresql-dev musl-dev && \
    # https://cryptography.io/en/latest/installation/#building-cryptography-on-linux
    apk add --update --no-cache libressl-dev musl-dev libffi-dev && \
    /py/bin/pip install -r /tmp/requirements.txt && \
    # if DEV arg is set to true install requirements.dev
    if [ $DEV = "true" ]; \
    then /py/bin/pip install -r /tmp/requirements.dev.txt; \
    fi && \
    rm -rf /tmp && \
    apk del \
    libressl-dev \
    musl-dev \
    libffi-dev \
    .tmp-build-deps && \
    # add user to docker image (to don't have to use root user)
    adduser \
    --disabled-password \
    --no-create-home \
    django-user

# update path environment variable (to run python command automatically
# from virtual env)
ENV PATH="/py/bin:$PATH"
# specify user that we switching to (before that we used root user)
USER django-user