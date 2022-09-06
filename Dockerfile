FROM ghcr.io/divideprojects/docker-python-base:latest
WORKDIR /app
COPY pyproject.toml poetry.lock .
RUN poetry export -f requirements.txt --without-hashes --output requirements.txt \
    && pip install --disable-pip-version-check -r requirements.txt
COPY . .
ENTRYPOINT ["python3"]
CMD ["-m", "vidmergebot"]
