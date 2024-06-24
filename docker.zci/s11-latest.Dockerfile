FROM registry.opensuse.org/suse/templates/images/sle-12-sp4/base/images/sle12:sp4
ARG CI_UID CI_GID

RUN rm /etc/zypp/repos.d/*.repo
RUN zypper --non-interactive ar --gpgcheck-allow-unsigned -f http://dist.suse.de/ibs/SUSE:/SLE-12:/GA/standard         s12GA
RUN zypper --non-interactive ar --gpgcheck-allow-unsigned -f http://dist.suse.de/ibs/SUSE:/SLE-12:/Update/standard     s12Up
RUN zypper --non-interactive ar --gpgcheck-allow-unsigned -f http://dist.suse.de/ibs/SUSE:/SLE-12-SP1:/GA/standard     s12sp1GA
RUN zypper --non-interactive ar --gpgcheck-allow-unsigned -f http://dist.suse.de/ibs/SUSE:/SLE-12-SP1:/Update/standard s12sp1Up
RUN zypper --non-interactive ar --gpgcheck-allow-unsigned -f http://dist.suse.de/ibs/SUSE:/SLE-12-SP2:/GA/standard     s12sp2GA
RUN zypper --non-interactive ar --gpgcheck-allow-unsigned -f http://dist.suse.de/ibs/SUSE:/SLE-12-SP2:/Update/standard s12sp2Up
RUN zypper --non-interactive ar --gpgcheck-allow-unsigned -f http://dist.suse.de/ibs/SUSE:/SLE-12-SP3:/GA/standard     s12sp3GA
RUN zypper --non-interactive ar --gpgcheck-allow-unsigned -f http://dist.suse.de/ibs/SUSE:/SLE-12-SP3:/Update/standard s12sp3Up
RUN zypper --non-interactive ar --gpgcheck-allow-unsigned -f http://dist.suse.de/ibs/SUSE:/SLE-12-SP4:/GA/standard     s12sp4GA
RUN zypper --non-interactive ar --gpgcheck-allow-unsigned -f http://dist.suse.de/ibs/SUSE:/SLE-12-SP4:/Update/standard s12sp4Up
RUN zypper --non-interactive ar --gpgcheck-allow-unsigned -f http://dist.suse.de/ibs/SUSE:/SLE-12-SP5:/GA/standard     s12sp5GA
RUN zypper --non-interactive ar --gpgcheck-allow-unsigned -f http://dist.suse.de/ibs/SUSE:/SLE-12-SP5:/Update/standard s12sp5Up
RUN zypper --non-interactive --gpg-auto-import-keys ref
RUN zypper --non-interactive --ignore-unknown in --no-recommends openssh sudo man tar git osc gcc-c++ cmake dejagnu doxygen asciidoc glibc-locale \
    augeas-devel boost-devel libcurl-devel gettext-tools glib2-devel libcurl-devel \
    libexpat-devel libproxy-devel libxml2-devel libopenssl-devel popt-devel python-devel \
    protobuf-devel readline-devel rpm-devel ruby-devel yaml-cpp-devel zlib-devel
# S11 specific
RUN zypper --non-interactive in --no-recommends check-devel graphviz bzip2

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
