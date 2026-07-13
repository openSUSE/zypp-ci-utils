import time, glob, json
from .Cmd import *

# Remove a TESTFAKE branch:
# git checkout slfo-main; git push -d origin TESTFAKE; git branch -D TESTFAKE
#======================================================================
def guessVersionFromTarball( tar ):
    # Guess version from tarball
    m = re.search( '-([^-]*)\.tar\.', tar )
    if m is None:
        raise Exception( f"guessVersionFromTarball: no version in {tar}" )
    return m[1]

#======================================================================
class Gitea( Cmd ):
    #verbosity = Cmd.SILENT
    USER = "anonymous"      # Owner of the forks
    _bscmd = ("git-obs",)   # the default

    @property
    def _cmd( self ):
        return ( *self._bscmd, *self._args )

    @classmethod
    def Pkg( cls, pkg ):   # package factory
        return _Pkg( cls, pkg )


#======================================================================
class _GiteaWorkspace( CmdWorkspace ):
    def __init__( self, cmdtype, wsPath ):
        if type(cmdtype) is not type or not issubclass( cmdtype, Gitea ):
            raise TypeError( f"{type(self).__name__}: BAD {type(cmdtype)} for cmdtype" )
        super().__init__( cmdtype, wsPath )

    @property
    def GITEAUSER( self ):
        return self.cmdtype.USER

    @property
    def gitobs( self ):         # git-obs: needs cwd=
        return self.cmdtype

    def git( self, *args ):     # git: operates in self.wsDir
        return Cmd( "git", "-C", self.wsDir, *args )

    @property
    def wsName( self ):
        return self.cmdtype.__name__

#======================================================================
class _Pkg( _GiteaWorkspace ):
    def __init__( self, cmdtype, pkg ):
        if type(pkg) is not str:
            raise TypeError( f"{type(self).__name__}: BAD {type(pkg)} pkg" )
        super().__init__( cmdtype, pkg )
        self.pkg = pkg  # str

    def __str__( self ):
        return f"{self.wsName}:/{self.pkg}"

    #======================================================================
    # gitobs

    def assertCheckout( self ):
        if not os.path.isdir( os.path.join( self.wsDir, ".git" ) ):
            Bprint( self.TAG, "assertCheckout" )
            self.assertWsDir()
            if not self.gitobs( "repo", "clone", f"{self.GITEAUSER}/{self.pkg}" ).tryrun( cwd=self.wsRoot ):
                raise Exception( f"Missing fork? (git-obs repo fork pool/{self.pkg})" )

    def getOpenPRs( self, prbranch, *, state="open", quiet=True ):
        # return the open PRs ("requests" list from json)
        out = self.gitobs( "pr", "list", "--export", "--state", state, "--target-branch", prbranch, f"pool/{self.pkg}" ).stdout( quiet=quiet )
        res = json.loads( out.asString() )
        # [
        #     {
        #         "owner": "pool",
        #         "repo": "libzypp",
        #         "requests": [
        #             {
        #                 "allow_maintainer_edit": true,
        if res:
            return res[0]["requests"]
        else:
            return []

    def fileNewPr( self, prbranch, *, title=None, description="." ):
        if title is None:
            raise Exception( f"{self}: fileNewPr {prbranch}: missing title" )
        self.gitobs( "pr", "create",
                    "--source-owner",  self.GITEAUSER,
                    "--source-repo",   self.pkg,
                    "--source-branch", prbranch,
                    "--target-branch", prbranch,
                    "--title", title, "--description", description ).run()

    def updatePR( self, ownerRepoPull, *, title=None, description=None ):
        # ownerRepoPull is <owner>/<repo>#<pull-request-number>
        # like pool/libzypp#8 (as returned by getOpenPRs)
        if title is None:
            raise Exception( f"{self}: updatePR {ownerRepoPull}: missing title" )
        if description is None:
            optDescr = tuple()
        else:
            optDescr = ( "--description", description )
        self.gitobs( "pr", "set", ownerRepoPull, "--title", title, *optDescr ).run()

    #======================================================================
    # git

    @property
    def currentBranch( self ):
        # Branch currently checked out.
        return self.git( "rev-parse", "--abbrev-ref", "HEAD" ).stdout( quiet=True ).theLine()

    def isLocalBranch( self, branch ):
        return bool(self.git( "show-ref", f"heads/{branch}" ).tryrun( quiet=True ))

    def isRemoteBranch( self, branch, *, remote=None ):
        if remote is not None:
            branch = f"{remote}/{branch}"
        return bool(self.git( "show-ref", f"remotes/{branch}" ).tryrun( quiet=True ))

    def isUnknownBranch( self, branch ):
        # neither local nor remotes
        return not bool(self.git( "show-ref", branch ).tryrun( quiet=True ))

    def isAncestor( self, oldcommit, newcommit ):
        # True if oldcommit is an ancestor of newcommit (incl. being equal)
        return bool(self.git( "merge-base", "--is-ancestor", oldcommit, newcommit ).tryrun( quiet=True ))

    def strictAncestor( self, oldcommit, newcommit ):
        # True  if oldcommit is a strict ancestor of newcommit (not equal)
        # False if oldcommit equals newcommit
        # Exception otherwise (unrelated or old newer than new)
        if self.isAncestor( oldcommit, newcommit ):
            return not self.isAncestor( newcommit, oldcommit ) # not equal
        raise Exception( f"{self}: {oldcommit} is no ancestor of {newcommit}; reverse {self.isAncestor( newcommit, oldcommit )}" )

    def commitId( self, commit ):
        return self.git( "describe", "--always", "--long", commit ).stdout( quiet=True ).theLine()

    def commitIdAnd( self, commit ):
        # tuple (id,commit) as convenience. id for compare, commit fro logging
        return ( self.commitId( commit ), commit )

    @property
    def guessVersion( self ):
        # Guess version from tarball in CWD
        tar = glob.glob( f"{self.wsDir}/{self.pkg}-*.tar.*" )
        if len(tar) != 1:
            raise Exception( f"{self}: guessVersion tar matches {tar}" )
        return guessVersionFromTarball( tar[0] )

    #======================================================================
    def fetch( self, *, threshold=0 ):
        self.assertCheckout()
        if threshold:
            fetchLog = os.path.join( self.wsDir, ".git/FETCH_HEAD" )
            try:
                since = int( time.time() - os.path.getmtime( fetchLog ) ) // 60
                if since < threshold:
                    Cprint( self.TAG, f"Next fetch in {threshold-since} min." )
                    return
            except FileNotFoundError:
                pass    # not yet fetched at all

        Bprint( self.TAG, "fetch" )
        self.git( "fetch", "--porcelain", "--all" ).run()


    def assertCleanBranch( self, branch, *, forceAt=None ):
        # Create or checkout local branch (always hard reset).
        # Optionally force reset to forceAt. Assert no local
        # changes. Not even untracked (which could be added
        # accidentally).
        Bprint( self.TAG, "assertCleanBranch", branch )
        if self.isLocalBranch( branch ):
            self.git( "checkout", branch ).run( quiet=True )
        else:
            self.git( "checkout", "-b", branch ).run( quiet=True )
        # properly hard reset the branch to it's remote (created if missing)
        if self.isRemoteBranch( branch, remote="origin" ):
            if forceAt is None: forceAt = f"origin/{branch}"
            self.git( "reset", "--hard", forceAt ).run()
        else:
            if forceAt is None: forceAt = "origin/HEAD"
            self.git( "reset", "--hard", forceAt ).run()
            self.git( "push" ).run()

        out = self.git( "status", "--porcelain" ).stdout()
        if out: # clean if no output from "status"
            raise Exception( f"{self}: Checkout not clean." )

    def statChanges( self, oldcommit, newcommit=None, *, quiet=False ):
        # Return any --name-status output like
        #   D  libzypp-17.38.13.tar.bz2
        #   A  libzypp-17.38.14.tar.bz2
        #   M  libzypp.changes
        #   M  libzypp.spec
        # If not quiet, pretty print the status and show the pkg.changes diff
        # if it was modified.
        Bprint( self.TAG, "statChanges", oldcommit, "CWD" if newcommit is None else newcommit )
        commitrange = oldcommit if newcommit is None else f"{oldcommit}..{newcommit}"

        ret = self.git( "diff", "--name-status", commitrange ).stdout( stdout='^[^#]', quiet=True ) # suppress #-lines in capture
        if not quiet:
            if ret:
                for line in ret.byLine():
                    if line[0] == "D":
                        Rprint( line )
                    elif line[0] == "A":
                        Gprint( line )
                    else:
                        Bprint( line )
                mychanges = f"{self.pkg}.changes"
                if ret.theLine( mychanges, missingOk=True ):
                    out = self.git( "diff", commitrange, mychanges ).stdout( stdout="^[+-@]", quiet=True )
                    skip = True
                    for line in out.byLine():
                        if skip:
                            if line[0] == "@":
                                skip = False
                            else:
                                continue
                        if line[0:1] == "+":
                            Gprint( line )
                        elif line[0:1] == "-":
                            Rprint( line )
                        else:
                            Cprint( line )
            else:
                Cprint( "No Changes" )

        return ret

    def extractStatChanges( self, *args, **kwargs ):
        out = self.statChanges( *args, **kwargs )
        # Extract tuple from statChanges output
        # D  zypp-plugin-0.6.6.tar.bz2
        # A  zypp-plugin-0.6.7.tar.bz2
        # M  zypp-plugin.changes
        curVersion = None  # if D
        newVersion = None  # if A
        newChanges = None  # if .changes (None if up-to-date)
        if out:
            newChanges = bool(out.theLine( f"{self.pkg}.changes", missingOk=True ))
            delv = out.theLine( f"^D\s*{self.pkg}-.*\.tar\.", missingOk=True )
            if delv:
                # expecting a deleted and an added tarball/version
                curVersion = guessVersionFromTarball( delv )
                newVersion = guessVersionFromTarball( out.theLine( f"^A\s*{self.pkg}-.*\.tar\." ) )
        return ( curVersion, newVersion, newChanges )

