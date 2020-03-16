FROM python:3.8-alpine
ARG CONFIG

ENV ANYREPO_CONFIG=/usr/local/share/anyrepo/config.toml
COPY . /app/
WORKDIR /app/

RUN apk add -U build-base \
        openldap-dev \
        python3-dev \
        libffi-dev \
        libressl-dev \
        postgresql-dev
RUN pip install -r /app/requirements.txt
RUN pip install psycopg2

RUN mkdir -p "$(dirname ${ANYREPO_CONFIG})"
RUN echo "${CONFIG}" > "${ANYREPO_CONFIG}"
EXPOSE 8888

ENTRYPOINT ["gunicorn", "-b", "0.0.0.0:8888", "app:app"]
