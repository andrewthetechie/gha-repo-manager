# Distroless runs python 3.9.2
FROM python:3.11-slim AS builder
ADD Docker/builder/rootfs /
ADD repo_manager /app/repo_manager
ADD main.py /app/main.py
WORKDIR /app

# We are installing a dependency here directly into our app source dir
RUN pip install --target=/app -r /requirements.txt

FROM python:3.11-slim-bullseye as python-base

# Update the base image
RUN apt-get update && apt-get upgrade -y

# Setup a non-root user
ARG NONROOT_USER="op"
ARG NONROOT_GROUP="op"

RUN groupadd ${NONROOT_GROUP}
RUN useradd -m ${NONROOT_USER} -g ${NONROOT_GROUP}

USER ${NONROOT_USER}
ENV PATH="/home/${NONROOT_USER}/.local/bin:${PATH}"
WORKDIR /home/${NONROOT_USER}
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONFAULTHANDLER 1

# upgrade pip and virtualenv
RUN pip install --upgrade pip && \
    pip install --no-warn-script-location --upgrade virtualenv

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

# Add some system utils
COPY --from=python-base /bin/echo /bin/echo
COPY --from=python-base /bin/rm /bin/rm
COPY --from=python-base /bin/sh /bin/sh

# Copy over the app
COPY --from=builder /app /app
WORKDIR /app
ENV PYTHONPATH /app

# non root user stuff
RUN echo "op:x:1000:op" >> /etc/group
RUN echo "op:x:1001:" >> /etc/group
RUN echo "op:x:1000:1001::/home/op:" >> /etc/passwd

# Remove shell utils and pip
RUN rm /bin/sh /bin/echo /bin/rm

# default to running as non-root, uid=1000
USER op

# Add /lib/libs to our path
ENV LD_LIBRARY_PATH="/lib/libs:${LD_LIBRARY_PATH}"
# Add the app path to our path
ENV PATH="/app/bin:${PATH}"
# Add the app path to your python path
ENV PYTHONPATH="/app:${PYTHONPATH}"
# standardise on locale, don't generate .pyc, enable tracebacks on seg faults
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONFAULTHANDLER 1

CMD ["python", "/app/main.py"]
