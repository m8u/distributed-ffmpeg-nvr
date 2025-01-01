ARG PYTHON_VERSION="3.13"

FROM python:${PYTHON_VERSION}-alpine

WORKDIR /app

RUN apk add ffmpeg

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=${PYTHONPATH}:/app/src

COPY pyproject.toml .

RUN pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install

COPY . .

ENTRYPOINT ["python", "src/main.py"]
