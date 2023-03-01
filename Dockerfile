FROM ghcr.io/divkix/docker-python-base:latest
WORKDIR /app
COPY . .
RUN poetry export -f requirements.txt --without-hashes --output requirements.txt \
    && pip install --disable-pip-version-check -r requirements.txt
ENTRYPOINT ["python3"]
CMD ["-m", "vidmergebot"]
