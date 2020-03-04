FROM python:3.8
ARG CONFIG

ENV ISSUEBOT_CONFIG=/usr/local/share/issuebot/config.toml
COPY . /app/
WORKDIR /app/
RUN pip install -r /app/requirements.txt

RUN mkdir -p "$(dirname ${ISSUEBOT_CONFIG})"
RUN echo "${CONFIG}" > "${ISSUEBOT_CONFIG}"
EXPOSE 8888

ENTRYPOINT ["gunicorn", "-b", "0.0.0.0:8888", "app"]
