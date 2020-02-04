FROM python:3

COPY . /app/
WORKDIR /app/
RUN pip install -r /app/requirements.txt

ENTRYPOINT ["flask", "run", "--host=0.0.0.0"]
