#! /bin/bash
# Build node setup to be parsed from .bashrc

Z_HOST=$(head -n 1 ~/zypp-ci-label | grep '^zypp-[a-z0-9._-]\+$')
test -n "$Z_HOST" && {

  export Z_HOST
  export Z_LABEL=${Z_HOST#zypp-}

}
