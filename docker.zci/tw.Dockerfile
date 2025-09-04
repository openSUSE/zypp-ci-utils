FROM registry.opensuse.org/opensuse/tumbleweed
ARG CI_UID CI_GID

RUN zypper --non-interactive --gpg-auto-import-keys ref
RUN zypper --non-interactive --no-refresh dup --no-recommends --remove-orphaned
RUN zypper --non-interactive --no-refresh --ignore-unknown in --no-recommends openssh shadow sudo man tar git osc gcc-c++ cmake dejagnu doxygen asciidoc \
    glibc-locale augeas-devel boost-devel libboost_program_options-devel libboost_test-devel libboost_thread-devel \
    libcurl-devel gettext-tools glib2-devel libcurl-devel libgpgme-devel libzck-devel libsigc++2-devel asciidoc \
    libexpat-devel libproxy-devel libxml2-devel libopenssl-devel popt-devel python-devel 'rubygem(asciidoctor)' \
    protobuf-devel readline-devel rpm-devel ruby-devel vsftpd yaml-cpp-devel zlib-devel bzip2 \
    nginx FastCGI-devel squid
RUN zypper --non-interactive --no-refresh --ignore-unknown in --no-recommends -- diffutils -busybox-diffutils
# just for syncing DOCs to doc.opensuse.org
# RUN zypper --non-interactive --no-refresh --ignore-unknown in --no-recommends rsync

ARG USER=zci
RUN groupadd --gid ${CI_GID} zci
RUN useradd --home-dir /home/zci --no-create-home --gid zci --uid ${CI_UID} ${USER}
RUN echo "%zci ALL=(ALL) NOPASSWD: ALL" >/etc/sudoers.d/zci

WORKDIR /root
RUN echo 'export PATH="$HOME/bin:/usr/local/sbin:/usr/local/bin:$PATH"' >>.bashrc
RUN echo 'export PS1="\w (\$?)# "' >>.bashrc
RUN echo 'alias ll="ls -l"' >>.bashrc

USER ${USER}
WORKDIR /home/zci
RUN mkdir -m 0700 .ssh
COPY --chown=${USER}:zci bashrc .bashrc
COPY --chown=${USER}:zci --chmod=0600 ssh_known_hosts .ssh/known_hosts
COPY --chown=${USER}:zci ZCI bin/
COPY --chown=${USER}:zci ZCIbuild bin/
