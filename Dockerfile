FROM python:3.13.6-slim@sha256:2a928e11761872b12003515ea59b3c40bb5340e2e5ecc1108e043f92be7e473d
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 TEST_TMPDIR=/tmp
WORKDIR /app
COPY requirements.lock .
RUN python -m pip install --no-cache-dir --only-binary=:all: --require-hashes -r requirements.lock \
    && useradd --uid 10001 --create-home runner \
    && chown runner:runner /app
COPY --chown=runner:runner vk_api ./vk_api
COPY --chown=runner:runner jconfig ./jconfig
COPY --chown=runner:runner tests ./tests
USER 10001:10001
CMD ["python", "-m", "unittest", "discover", "-s", "tests", "-v"]
