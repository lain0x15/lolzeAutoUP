FROM python:3.12-slim

WORKDIR /usr/src/app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

ENV NAME World

ENTRYPOINT ["python"]

CMD ["main.py"]