#! /bin/bash
# Setup anf tools for Jenkins build scripts:
# . ~/zypp-ci-utils/bin/ci-profile.sh
##################################################
. ~/zypp-ci-utils/bin/ascii_art

function msg()
{ echo "$@"; }

function error_msg()
{ echo "ERROR: $@"; }

function error_exit()
{ error_msg "$@"; exit 1; }

function exit_check()
{
  local RET=$?
  if [ $RET == 0 ]; then
    ascii_good
  else
    ascii_bad $RET
  fi
}
trap "exit_check"	EXIT
#trap "error_exit \$?"	ERR

test -n "$Z_LABEL" || {
  error_exit "Bad hostsetup: no Z_LABEL"
}

###################################################
# config variables and their defaults

export Z_ALLOWSUBMIT="${Z_ALLOWSUBMIT:-1}"		# Whether to allow submission to obs at all
export Z_OBS_PROJECT					# if empty autodetect from Z_LABEL
export Z_DOC_PROJECT					# if empty autodetect from Z_LABEL

case "$Z_LABEL" in
    head)
      Z_OBS_PROJECT="${Z_OBS_PROJECT:-zypp:Head}"
      Z_DOC_PROJECT="${Z_DOC_PROJECT:-HEAD}"
      ;;

    s15)
      Z_OBS_PROJECT="${Z_OBS_PROJECT:-zypp:SLE-15-Branch}"
      Z_DOC_PROJECT="${Z_DOC_PROJECT:-SLE15}"
      ;;

    s12sp3)
      Z_OBS_PROJECT="${Z_OBS_PROJECT:-zypp:SLE-12-SP3-Branch}"
      Z_DOC_PROJECT="${Z_DOC_PROJECT:-SLE12SP3}"
      ;;
    s12sp2)
      Z_OBS_PROJECT="${Z_OBS_PROJECT:-zypp:SLE-12-SP2-Branch}"
      Z_DOC_PROJECT="${Z_DOC_PROJECT:-SLE12SP2}"
      ;;
    s12sp1)
      Z_OBS_PROJECT="${Z_OBS_PROJECT:-zypp:SLE-12-SP1-Branch}"
      Z_DOC_PROJECT="${Z_DOC_PROJECT:-SLE12SP1}"
      ;;
    s12)
      Z_OBS_PROJECT="${Z_OBS_PROJECT:-zypp:SLE-12-Branch}"
      Z_DOC_PROJECT="${Z_DOC_PROJECT:-SLE12}"
      ;;

    s11sp3)
      Z_OBS_PROJECT="${Z_OBS_PROJECT:-zypp:SLE-11-SP3-Branch}"
      Z_DOC_PROJECT="${Z_DOC_PROJECT:-SLE11SP3}"
      ;;
    s11sp2)
      Z_OBS_PROJECT="${Z_OBS_PROJECT:-zypp:SLE-11-SP2-Branch}"
      Z_DOC_PROJECT="${Z_DOC_PROJECT:-SLE11SP2}"
      ;;
  esac

# build related variables
export CMAKE_INSTALL_PREFIX="${CMAKE_INSTALL_PREFIX:-/usr}"
export CMAKEPARAS="${CMAKEPARAS:--DCMAKE_INSTALL_PREFIX=$CMAKE_INSTALL_PREFIX}"
export CLEANBUILD="${CLEANBUILD:-0}"
export MAKEJOBS="${MAKEJOBS:-4}"

# basic variabels
export CHECKOUTDIR="$WORKSPACE/checkout"
export ARTIFACTS="$WORKSPACE/artifacts"
export BUILDDIR="$WORKSPACE/build"
export BUILDPACKAGEDIR="$WORKSPACE/build/package"
export OBSDIR="$WORKSPACE/obs"

# cleanup leftovers from a previous broken build
rm -rf "$WORKSPACE"/copy-to-slave*.dir
rm -rf "$ARTIFACTS"
if [ "$CLEANBUILD" != "0" ]; then
  rm -rf "$BUILDDIR"
else
  rm -rf "$BUILDPACKAGEDIR"
  fi
rm -rf "$OBSDIR"

mkdir -p "$ARTIFACTS"
mkdir -p "$BUILDDIR"
mkdir -p "$OBSDIR"

##################################################
# Return if the jobs parent folder matches
# the nodes Z_LABEL. E.g. on a 'head' node only
# head/* jobs may submitt to OBS.
function ci_assert_host_job_label()
{
  local JOB_LABEL="$(basename "$(dirname "$JOB_NAME")")"
  test "$JOB_LABEL" == "$Z_LABEL" || {
    error_exit "$JOB_LABEL-jobs must not submitt from $Z_LABEL-nodes"
  }
}

function isNotEmptyDir()
{
  local DIR="$1"
  test -d "$DIR"			|| return 1
  test $(ls "$DIR" | wc -l) -gt 0	|| return 1
  return 0
}

##################################################

function ci_build()
{
  pushd "$BUILDDIR"
  msg "==> Building"

  # cmake won't put headers found in /usr/include into the make depends.
  test -e /usr/local/include/solv || ln -s /usr/include/solv/ /usr/local/include/solv
  test -e /usr/local/include/zypp || ln -s /usr/include/zypp/ /usr/local/include/zypp
  export CMAKE_PREFIX_PATH="/usr/local/include:/usr/include"

  #
  case "$Z_LABEL" in
    head|s15*)
	case "$JOB_BASE_NAME" in
	  *-libzypp)
	    CMAKEPARAS="$CMAKEPARAS -DENABLE_ZSTD_COMPRESSION=1"
	    CMAKEPARAS="$CMAKEPARAS -DENABLE_ZCHUNK_COMPRESSION=1"
	    ;;
	esac
        ;;
  esac

  cmake $CMAKEPARAS "$CHECKOUTDIR"
  if [ "$1" == "clean" ]; then
    make clean
  fi
  make -j $MAKEJOBS

  popd
}

##################################################

function ci_build_make()
{
  pushd "$CHECKOUTDIR"
  msg "==> Building (legacy make)"

  if [ -f Makefile.cvs ]; then
    make -f Makefile.cvs
  fi
  make -j $MAKEJOBS

  if [ -d package ]; then
    make package-local
    cp -av package/* "$ARTIFACTS"/
  else
    error_exit "No 'package' subdirectory found!!"
  fi

  msg "==> Installing (legacy make)"
  make install

  popd
}

##################################################

function ci_runtest()
{
  pushd "$BUILDDIR"
  msg "==> Testing"

  if [ -f "CTestTestfile.cmake" ]; then
    if [ -d "tests" ]; then
      pushd tests
    elif [ -d "test" ]; then
      pushd test
    else
      error_exit "No tests found!!"
    fi
    export BOOST_TEST_CATCH_SYSTEM_ERRORS=no
    export CTEST_OUTPUT_ON_FAILURE=1
    make -j $MAKEJOBS
    make test
    popd
  else
    error_exit "No tests found!!"
  fi

  popd
}

##################################################

function ci_install()
{
  pushd "$BUILDDIR"
  msg "==> Building Source Package"

  if [ -d "$BUILDPACKAGEDIR" ]; then
    make srcpackage_local
    cp -av "$BUILDPACKAGEDIR"/* "$ARTIFACTS"/
  else
    error_exit "No 'package' subdirectory found!!"
  fi

  msg "==> Installing"
  make install

  if [ "$JOB_BASE_NAME" == "20-libzypp" ]; then
    msg "==> Clean old libs"
    find "$BUILDDIR"/zypp/libzypp.so.* /usr/lib64/libzypp.so.* -type f -ctime +5 | xargs --no-run-if-empty rm
    ldconfig
  fi

  popd
}

##################################################
# ci_submitt [SRC_PACKAGE]
#
# Submitt this or some job in the same parent dir.
# As a safety check the hosts Z_LABEL must match the
# parent folder name (i.e. 'head' jobs may submitt on
# 'head' nodes only).
#
# This is how to submitt to an non-default Z_OBS_PROJECT
# and how to submitt from a job outside the Z_LABEL folder:
#
#	# fake jobname folder to satisfy submission checks
#	Z_OBS_PROJECT="systemsmanagement:spacewalk"
#	JOB_NAME="zypp/head/$JOB_BASE_NAME" ci_submitt
#
function ci_submitt()
{
  if [ "$Z_ALLOWSUBMIT" == "0" ]; then
    msg "==> Submissions are globally disabled!!!"
    return 0
  fi
  ci_assert_host_job_label	# No submission with wrong label

  # Configured OBS project to submitt to
  test -n "$Z_OBS_PROJECT" || {
    error_exit "No Z_OBS_PROJECT definition (obs project to submit to)"
  }

  SRC_PACKAGE="${1:-$JOB_BASE_NAME}"	# Jenkins job name
  test -n "$SRC_PACKAGE" -a -d "$WORKSPACE/../$SRC_PACKAGE" || {
    error_exit "Oops! No Jenkins job '$SRC_PACKAGE'?"
  }

  OBS_PACKAGE="${SRC_PACKAGE#[0-9]*-}"	# Z_OBS_PROJECTs package name
  test -n "$OBS_PACKAGE" || {
    error_exit "Oops! No Z_OBS_PROJECT package name?"
  }

  SRC_PACKAGEDIR="$WORKSPACE/../$SRC_PACKAGE/artifacts"	# Jenkins jobs last artifacts
  isNotEmptyDir "$SRC_PACKAGEDIR" || {
    error_exit "Oops! No Jenkins job '$SRC_PACKAGE' artifacts dir?"
  }

  # ============================================
  # SRC_PACKAGEDIR/* ==> obs://Z_OBS_PROJECT/OBS_PACKAGE
  echo "$SRC_PACKAGE"
  echo "$Z_OBS_PROJECT"
  echo "$OBS_PACKAGE"
  echo "$SRC_PACKAGEDIR"

  # build the osc command - API and rc-file may be overwritten in project
  OSCBIN="/usr/bin/osc"
  OSCAPI="${OSCAPI:-https://api.opensuse.org}"
  OSCRC="${OSCRC:-~/.ssh/ci-oscrc}"
  OSC="$OSCBIN -A $OSCAPI -c $OSCRC"

  # get data from obs
  pushd "$OBSDIR"
  rm -rf "$Z_OBS_PROJECT/$OBS_PACKAGE"
  $OSC co -u "$Z_OBS_PROJECT" "$OBS_PACKAGE"

  # format the spec file the same way the build service does in order
  # to avoid unneeded submissions because files differ
  PREPARESPEC="/usr/lib/obs/service/format_spec_file.files/prepare_spec"
  if [ -x $PREPARESPEC ]; then
    for specfile in "$SRC_PACKAGEDIR"/*.spec; do
      tmpfile="$(mktemp)"
      $PREPARESPEC "$specfile" >"$tmpfile"
       mv "$tmpfile" "$specfile"
    done
  fi

  # submitt if there are changes
  if ! copy_artifacts "$SRC_PACKAGEDIR" "$Z_OBS_PROJECT/$OBS_PACKAGE"; then
    echo "The current and new package are the same - not submitting to OBS."
  else
    echo "The current and new package differ - submitting to OBS now."
    pushd "$Z_OBS_PROJECT/$OBS_PACKAGE"

    # doit!
    ${OSC} addremove
    ${OSC} ci -m "Update to last successful build$(augmentGitCommitVersion "$SRC_PACKAGE")"

    popd
  fi

  # Remember the stack we processed (?)
  if [ "$JOB_BASE_NAME" == "40-submitt-stack" ]; then
    cp -av "$SRC_PACKAGEDIR"/* "$ARTIFACTS"
  fi

  popd
}


function copy_artifacts()
{
  local ARTD="$1"
  test -d "$ARTD" || { echo "No arifacts dir '$ARTD'"; return 1; }
  local TRGD="$2"
  test -d "$TRGD" || { echo "No target dir '$TRGD'"; return 1; }

  # track changes so we can later decide whether we must tar_diff.
  local DIFFS=0

  # check excess target files (usually new tarball version)
  for F in "$TRGD"/*; do
    local STEM="$(basename "$F")"
    test -f "$ARTD/$STEM" || {
      rm -f -v "$F" || return 2
      DIFFS=1
    }
  done

  if [ $DIFFS == 1 ]; then
    cp -v "$ARTD"/* "$TRGD" || return 3
    return 0
  fi

  # check non-tarball changes
  TARDIFF=""
  for F in "$ARTD"/*; do
    local STEM="$(basename "$F")"
    test -f "$TRGD/$STEM" || {
      # new artifact
      DIFFS=1
      break
    }
    diff -q "$F" "$TRGD/$STEM" && {
      # no changes
      continue
    }
    case "$STEM" in
      *.tar.*|*.tar|*.tgz|*.tbz2)
    # tarball diff not necessarily implies content change
    TARDIFF="$TARDIFF $STEM"
        ;;
      *)
        DIFFS=1
    break
    ;;
    esac
  done
  if [ $DIFFS == 1 ]; then
    cp -v "$ARTD"/* "$TRGD" || return 3
    return 0
  fi

  # finally do tardiffs
  test -n "$TARDIFF" && {
    for STEM in $TARDIFF; do
      local TDIR=$(mktemp -d) || return 4
      tar_diff "$ARTD/$STEM" "$TRGD/$STEM" "$TDIR" || {
    rm -rf "$TDIR"
        DIFFS=1
    break
      }
      rm -rf "$TDIR"
    done

    if [ $DIFFS == 1 ]; then
      cp -v "$ARTD"/* "$TRGD" || return 3
      return 0
    fi
  }

  echo "No changes."
  return 1
}

function tar_diff() {
  local LTAR="$1"
  local RTAR="$2"
  local TDIR="$3"
  test -d "$TDIR" || { echo "No tmpdir for tar_diff '$TDIR'"; return 1; }

  mkdir "$TDIR/L";
  tar_cat "$LTAR" | tar xf - -C "$TDIR/L" || return 2
  mkdir "$TDIR/R";
  tar_cat "$RTAR" | tar xf - -C "$TDIR/R" || return 2

  if diff -r -q "$TDIR/L" "$TDIR/R"; then
    echo "Content $LTAR and $RTAR is the same"
    return 0
  else
    echo "Content $LTAR and $RTAR differs"
    return 5
  fi
}

function tar_cat() {
    case "$1" in
      *.gz|*.tgz)   gzip -dc "$1" ;;
      *.bz2|*.tbz2) bzip2 -dc "$1" ;;
      *)            cat "$1" ;;
    esac
}

# If we find a git checkout, print branch info and
# commit revision.
function augmentGitCommitVersion()
{
  local SRC_PACKAGE=$1 ; shift    # Hudson job name
  local CHECKOUT_DIR=${WORKSPACE}/../${SRC_PACKAGE}/checkout

  test -d "$CHECKOUT_DIR" && ( #intentionally (
    cd "$CHECKOUT_DIR"
    git rev-parse --show-cdup >/dev/null 2>&1 && {
      # it's a a git repository:
      echo -e "\n$(git symbolic-ref -q HEAD | sed 's%.*/\([^/]*\)$%[\1]%') $(git log --pretty=oneline --relative HEAD^..HEAD)"
    }
  )
}

##################################################

function ci_libzypp_online_doc()
{
  pushd "$BUILDDIR"
  msg "==> Building libzypp online doc"

  # build
  cmake $CMAKEPARAS "$CHECKOUTDIR"
  test -d doc
  make doc_forced

  # publish
  if [ "$Z_ALLOWSUBMIT" == "0" ]; then
    msg "==> Submissions are globally disabled!!!"
    return 0
  fi
  ci_assert_host_job_label	# No submission with wrong label

  test -n "$Z_DOC_PROJECT" || {
    error_exit "No Z_DOC_PROJECT definition (directory name on documentation site)"
  }

  PROJECT="libzypp"

  DOCDIR="$BUILDDIR/doc"
  SYNCDIR="$BUILDDIR/doc/sync"
  AUTODOC="$BUILDDIR/doc/autodoc"
  HTMLDOC="$BUILDDIR/doc/autodoc/html"

  if [[ -d "$HTMLDOC" && `ls "$HTMLDOC"/ | wc -l` -gt 0 ]]; then
    rm -rf "$SYNCDIR/$PROJECT"
    mkdir -p "$SYNCDIR/$PROJECT"
    mv "$HTMLDOC" "$SYNCDIR/$PROJECT/$Z_DOC_PROJECT"

    SSHPARAMS=" -i $HOME/.ssh/docssh-id_rsa -p2206 -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no "
    rsync -e "ssh $SSHPARAMS" -dvlt --delete --no-p --no-g --chmod=ug+rw "$SYNCDIR/$PROJECT"                jdsn@gate.opensuse.org:/home/jdsn/rtfm.opensuse.org/htdocs/projects
    rsync -e "ssh $SSHPARAMS" -dvlt --delete --no-p --no-g --chmod=ug+rw "$SYNCDIR/$PROJECT/$Z_DOC_PROJECT" jdsn@gate.opensuse.org:/home/jdsn/rtfm.opensuse.org/htdocs/projects/"$PROJECT"
    rsync -e "ssh $SSHPARAMS" -rvlt --delete --no-p --no-g --chmod=ug+rw "$SYNCDIR/$PROJECT/$Z_DOC_PROJECT" jdsn@gate.opensuse.org:/home/jdsn/rtfm.opensuse.org/htdocs/projects/"$PROJECT"
  else
    error_exit "No html autodoc found to be synced to documentation site"
  fi

  popd
}

##################################################
