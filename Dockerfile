# Distroless runs python 3.9.2
FROM python:3.9.2-slim AS builder
ADD Docker/builder/rootfs /
ADD repo_manager /app/repo_manager
ADD main.py /app/main.py
WORKDIR /app

# We are installing a dependency here directly into our app source dir
RUN pip install --target=/app -r /requirements.txt

# A distroless container image with Python and some basics like SSL certificates
# https://github.com/GoogleContainerTools/distroless
FROM gcr.io/distroless/python3
COPY --from=builder /app /app
WORKDIR /app
ENV PYTHONPATH /app
CMD ["/app/main.py"]
