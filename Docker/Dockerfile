FROM python:3.11-slim AS python-base
ADD Docker/builder/rootfs /
ADD repo_manager /app/repo_manager
ADD main.py /app/main.py
WORKDIR /app

# We are installing a dependency here directly into our app source dir
RUN pip install --upgrade pip && \
    pip install --no-warn-script-location --upgrade virtualenv && \
    pip install --target=/app -r /requirements.txt


# use distroless/cc as the base for our final image
# lots of python depends on glibc
FROM gcr.io/distroless/cc-debian11

# Copy python from the python-builder
# this carries more risk than installing it fully, but makes the image a lot smaller
COPY --from=python-base /usr/local/lib/ /usr/local/lib/
COPY --from=python-base /usr/local/bin/python /usr/local/bin/python
COPY --from=python-base /etc/ld.so.cache /etc/ld.so.cache

# Add some common compiled libraries
# If seeing ImportErrors, check if in the python-base already and copy as below
# required by lots of packages - e.g. six, numpy, wsgi
# *-linux-gnu makes this builder work with either linux/arm64 or linux/amd64
COPY --from=python-base /lib/*-linux-gnu/libz.so.1 /lib/libs/
COPY --from=python-base /usr/lib/*-linux-gnu/libffi* /lib/libs/
COPY --from=python-base /lib/*-linux-gnu/libexpat* /lib/libs/

# Copy over the app
COPY --from=python-base /app /app


# Add /lib/libs to our path
ENV LD_LIBRARY_PATH="/lib/libs:${LD_LIBRARY_PATH}" \
# Add the app path to our path
    PATH="/app/bin:${PATH}" \
# Add the app path to your python path
    PYTHONPATH="/app:${PYTHONPATH}" \
# standardise on locale, don't generate .pyc, enable tracebacks on seg faults
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONFAULTHANDLER=1

CMD ["python", "/app/main.py"]
