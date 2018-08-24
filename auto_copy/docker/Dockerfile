FROM ubuntu
# taken from https://hub.docker.com/r/mantlepro/handbrake/
RUN apt-get update && apt-get install -y software-properties-common && \
    add-apt-repository ppa:stebbins/handbrake-releases && \
    add-apt-repository multiverse && \
    apt-get update
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y handbrake-cli libdvd-pkg libcdio-utils
RUN DEBIAN_FRONTEND=noninteractive dpkg-reconfigure libdvd-pkg


