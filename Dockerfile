FROM python:3.11-slim-bullseye AS builder
WORKDIR /app

# install build requirements
RUN apt-get update && apt-get install -y binutils patchelf build-essential scons upx

# copy the app
COPY ./ /app

# install python build requirements
RUN pip install --no-warn-script-location --upgrade virtualenv pip poetry pyinstaller staticx --constraint=package-requirements.txt

# build the app
RUN poetry build
# Install the app
RUN pip install dist/gha_repo_manager*.whl

# pyinstaller package the app
RUN python -OO -m PyInstaller -F repo_manager/main.py --name repo-manager --hidden-import _cffi_backend
# static link the repo-manager binary
RUN cd ./dist && \
    staticx -l $(ldconfig -p| grep libgcc_s.so.1 | awk -F "=>" '{print $2}' | tr -d " ") --strip repo-manager repo-manager-static && \
    strip -s -R .comment -R .gnu.version --strip-unneeded repo-manager-static
# will be copied over to the scratch container, pyinstaller needs a /tmp to exist
RUN mkdir /app/tmp


FROM scratch

ENTRYPOINT ["/repo-manager"]

COPY --from=builder /app/dist/repo-manager-static /repo-manager
COPY --from=builder /app/tmp /tmp
