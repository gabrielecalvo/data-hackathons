FROM python:3.11-slim-bullseye

ARG DOCKER_IMAGE_TAG
ENV DOCKER_IMAGE_TAG=$DOCKER_IMAGE_TAG
ENV PYTHONUNBUFFERED 1
ENV DEBIAN_FRONTEND noninteractive

RUN \
    apt-get update -yqq \
    && apt-get install -yqq gcc \
    # Python dependencies
    && pip install --no-cache-dir --upgrade pip setuptools poetry \
    && poetry config virtualenvs.create false \
    # Cleanup
    && rm -rf /var \
    && rm -rf /root/.cache  \
    && rm -rf /usr/lib/python2.7 \
    && rm -rf /usr/lib/x86_64-linux-gnu/guile \
    && rm -rf ~/.cache/pypoetry/{cache,artifacts}

WORKDIR /app/api

COPY poetry.lock pyproject.toml ./
RUN poetry install --no-root --only main --no-interaction --no-ansi

COPY . .
RUN poetry install --only-root --no-interaction --no-ansi


ENV HOST=0.0.0.0
ENV PORT=80

EXPOSE 80

CMD [ \
    "gunicorn", \
    "-c", \
    "gunicorn.conf.py", \
    "app.main:app" \
    ]
