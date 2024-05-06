FROM postgres:13
# install system packages for building postgres extensions
RUN apt-get update && apt-get install -y \
    less \
    make \
    vim \
    postgresql-server-dev-13 \
    postgresql-plpython3-13 \
    python3 \
    python3-pip \
    sudo \
    wget

# install a newer version of git
# these libraries are required just for installing a new version of git
RUN apt-get install -y \
    libcurl4-gnutls-dev \
    libexpat1-dev gettext \
    libz-dev \
    libssl-dev \
    asciidoc \
    xmlto \
    docbook2x
RUN cd /tmp \
 && wget https://www.kernel.org/pub/software/scm/git/git-2.30.1.tar.gz \
 && tar -xzf git-2.30.1.tar.gz \
 && cd git-2.30.1 \
 && ./configure \
 && make \
 && make install \
 && rm -rf /tmp/git-2.30.1

# install postgres extensions from source
RUN cd /tmp \
 && git clone https://github.com/postgrespro/rum \
 && cd rum \
 && git checkout 1.3.7 \
 && make USE_PGXS=1 \
 && make USE_PGXS=1 install \
 && rm -rf /tmp/rum

WORKDIR /tmp/db

RUN mkdir /data && chown postgres /data

# copy over the pagila database;
# we rename the files so that they get executed in the correct order
COPY schema.sql /docker-entrypoint-initdb.d/01.sql
