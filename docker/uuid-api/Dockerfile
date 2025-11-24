FROM python:3.13-slim-bookworm

LABEL description="UUID API Service"

ARG HOST_GID
ARG HOST_UID
ARG IMAGE_USER

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Change to directory that contains the Dockerfile
WORKDIR /usr/src/app

# The EXPOSE instruction informs Docker that the container listens on the specified network ports at runtime. 
# EXPOSE does not make the ports of the container accessible to the host.
# Here 5000 is for the uwsgi socket, 8080 for nginx
EXPOSE 5000 8080

# Update dependencies and install build dependencies
RUN apt-get update -y && \
    apt-get dist-upgrade -y && \
    apt-get install -y curl gcc gnupg2 ca-certificates lsb-release debian-archive-keyring

# Install nginx (https://nginx.org/en/linux_packages.html#Debian)
RUN \
    # import an official nginx signing key
    curl https://nginx.org/keys/nginx_signing.key | gpg --dearmor \
        | tee /usr/share/keyrings/nginx-archive-keyring.gpg >/dev/null && \
    # verify the signature contains the full fingerprint "573BFD6B3D8FBC641079A6ABABF5BD827BD9BF62", if not then fail
    gpg --dry-run --quiet --no-keyring --import --import-options import-show /usr/share/keyrings/nginx-archive-keyring.gpg | grep -q "573BFD6B3D8FBC641079A6ABABF5BD827BD9BF62" || \
    (echo "Signature verification failed!" && exit 1) && \
    # add the stable nginx repository
    echo "deb [signed-by=/usr/share/keyrings/nginx-archive-keyring.gpg] \
    http://nginx.org/packages/debian `lsb_release -cs` nginx" \
        | tee /etc/apt/sources.list.d/nginx.list && \
    # set up repository pinning to prefer nginx stable
    printf "Package: *\nPin: origin nginx.org\nPin: release o=nginx\nPin-Priority: 900\n" \
        | tee /etc/apt/preferences.d/99nginx >/dev/null && \
    apt-get update -y && \
    apt-get install -y nginx

COPY . .

# Install python dependencies
RUN pip install --upgrade pip setuptools wheel && \
    pip install uwsgi && \
    pip install -r src/requirements.txt

# Clean up unnecessary packages to reduce image size
RUN apt-get purge -y lsb-release gcc && \
    apt-get auto-remove -y

# Create the non-root user
RUN groupadd -g ${HOST_GID} ${IMAGE_USER} && \
    useradd -u ${HOST_UID} -m -g ${HOST_GID} -s /bin/bash ${IMAGE_USER}

# Ensure non-root user has access to the following directories
RUN touch /var/run/nginx.pid && \
    chown -R ${IMAGE_USER}:${IMAGE_USER} /etc/nginx/ && \
    chown -R ${IMAGE_USER}:${IMAGE_USER} /etc/nginx/conf.d/ && \
    chown -R ${IMAGE_USER}:${IMAGE_USER} /usr/lib/nginx/ && \
    touch /var/log/nginx/error.log && \
    chown -R ${IMAGE_USER}:${IMAGE_USER} /var/log/nginx && \
    chown -R ${IMAGE_USER}:${IMAGE_USER} /var/cache/nginx && \
    chown -R ${IMAGE_USER}:${IMAGE_USER} /var/run/nginx.pid && \
    chown -R ${IMAGE_USER}:${IMAGE_USER} /run/nginx.pid && \
    mv nginx/nginx.conf /etc/nginx/nginx.conf && \
    rm -rf nginx && \
    chown -R ${IMAGE_USER}:${IMAGE_USER} /usr/src/app

USER ${IMAGE_USER}

CMD ["./start.sh"]
