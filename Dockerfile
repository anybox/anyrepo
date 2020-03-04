FROM python:3.8
ARG CONFIG

ENV ANYREPO_CONFIG=/usr/local/share/anyrepo/config.toml
COPY . /app/
WORKDIR /app/
RUN pip install -r /app/requirements.txt

RUN mkdir -p "$(dirname ${ANYREPO_CONFIG})"
RUN echo "${CONFIG}" > "${ANYREPO_CONFIG}"
EXPOSE 8888

ENTRYPOINT ["gunicorn", "-b", "0.0.0.0:8888", "app"]
