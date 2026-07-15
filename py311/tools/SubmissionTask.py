from .Task import *
import os, glob
#======================================================================
#
# Obs:  Obs-zypp-Head -> origin/Obs-zypp-Head
# PRs:  origin/slfo* -> parent/slfo*
#
# on update (from obs):
# - sync obs:/zypp:Head to local Obs-zypp-Head branch
# - diff between Obs-zypp-Head <> origin/Obs-zypp-Head
#   is what would be the next submission.
#
# on submitt (to gitea):
# - submitt Obs-zypp-Head -> origin/Obs-zypp-Head
# - force reset origin/slfo* to origin/Obs-zypp-Head
# - file missing PRs origin/slfo* -> parent/slfo*
#
#======================================================================
class StepStat:
    # Sums up the diff between 2 commits (e.g. a running PR)
    # Constructed from Gitea.Pkg.extractStatChanges result:
    #   D  zypp-plugin-0.6.6.tar.bz2
    #   A  zypp-plugin-0.6.7.tar.bz2
    #   M  zypp-plugin.changes
    def __init__( self, statTuple=None ):   # Ddefault constructed is UP-TO-DATE!
        self.curVersion = None # None: Version did not change (might be set if current version is known)
        self.newVersion = None # None: Version did not change
        self.newChanges = None # None: Up-to-date; True if new .changes; False something else changed
        if statTuple is not None:
            self.curVersion, self.newVersion, self.newChanges = statTuple

    @property
    def mayUpdate( self ):
        # There is a version change and there are new .changes
        return self.newVersion is not None and self.newChanges

    def __bool__( self ):   # True if not up-to-date
        return self.newChanges is not None

    @property
    def LOGprint( self ):   # the color print for the status
        if self.mayUpdate:
            return Mprint
        return Cprint if self else Bprint

    def LOG( self, *args, post=() ):
        self.LOGprint( "###", *args, self, *post )

    def __str__( self ):
        if self:
            if self.mayUpdate:
                tag = "Update to"
            elif self.newVersion is None:
                tag = "New .changes" if self.newChanges else "Modified"
            else:
                tag = "No .changes"
        else:
            tag = "Up-to-date at"

        if self.newVersion is None:
            vers = self.curVersion if self.curVersion is not None else 'unchanged'
            return f": {tag:13} {vers:>9}"
        else:
            return f": {tag:13} {self.newVersion:>9} ({self.curVersion:})"

#======================================================================
class SubmissionTask:
    #======================================================================
    class Stats:
        # State of the git package:
        def __init__( self ):
            self.fromObs = None     # StepStat(OBS<>trg CWD)
            self.prbranches = {}    # per prbranch ( StepStat(trg<>origin), StepStat(origin<>parent), [runningPR(s)] )

        def ostat( self, pbranch ):
            return self.prbranches[pbranch][0]

        def pstat( self, pbranch ):
            return self.prbranches[pbranch][1]

        def runningPR( self, pbranch ):
            return self.prbranches[pbranch][2]

    #======================================================================
    class Fate:
        # Commit todo computed based on Stats:
        # - commitFromObs       Whether to commit trg CWD to trg
        # - toVersion           The new version (new from trg CWD or the current in trg
        # - per prbranch tuple:
        #     - updateOrigin    Whether to sync trg<>origin
        #     - needPR          Whether a PR origin<>parent should be running
        #     - havePR          Whether a PR origin<>parent is running
        #     - fromVersion     The current version in parent
        #
        # Submissions if not commitFromObs may only occur if trg<>origin is not
        # in sync or needed PRs are missing.
        def __init__( self, stats ):
            self.commitFromObs = stats.fromObs is not None and stats.fromObs.mayUpdate
            self.toVersion     = stats.fromObs.newVersion if self.commitFromObs else stats.fromObs.curVersion
            self.prbranches    = {}

            for prbranch in stats.prbranches:
                ostat, pstat, runningPR = stats.prbranches[prbranch]

                updateOrigin = bool(self.commitFromObs or ostat)   # ostat fixes the unwanted case that trg<>origin differ
                needPR       = bool(updateOrigin or pstat)         # this is what should be (git origin<>parent)
                havePR       = bool(runningPR)                     # actually running PR (from git-obs)
                fromVersion  = pstat.curVersion if pstat.curVersion is not None else ostat.curVersion if ostat.curVersion is not None else stats.fromObs.curVersion

                self.prbranches[prbranch] = ( updateOrigin, needPR, havePR, fromVersion )

    #======================================================================
    # WF:
    # - fill Stats (updateFromObs, submittStatus)
    # - setFateFromStats
    # - summarize or execute Fate
    def __init__( self, obsSourcePrj, giteaTarget, pkg, *, fetchDelay=0 ):
        self._obsSourcePrj = obsSourcePrj
        self._giteaTarget  = giteaTarget

        self.pkg = pkg                      # the package
        self.src = obsSourcePrj.Pkg( pkg )  # the Obs package checkout
        self.trg = giteaTarget.Pkg( pkg )   # The git package checkout
        self.trgbranch = obsSourcePrj.suggestGitBranchName()

        LOG_HEAD( "SubmissionTask", pkg, obsSourcePrj, "->", giteaTarget.__name__ )
        # Prepare a clean trgbranch for the obsSourcePrj.
        self.trg.fetch( threshold=fetchDelay )
        self.trg.assertCleanBranch( self.trgbranch )
        LOG_SEP()

        self.stats = self.Stats()

    def updateFromObs( self, *, taintedOk=False, update=True ):
        # taintedOk: Allow OBS checkout to have local changes (for testing)
        # noUpdate:  Dont't update from OBS at all and use local data (for testing)
        # Sync obsSourcePrj and stat what could be the next submission.
        # (diff between trgbranch <> origin/trgbranch)
        src = self.src
        trg = self.trg
        LOG_TASK( "updateFromObs", src, "->", trg )

        # checkout from obs
        if not update:
            Rprint( "***", "Not-update set: Skip obs checkout and use local data." )
        else:
            src.updateCheckout( taintedOk=taintedOk )

        # copy obs to gitea (hardlink)
        if update is None:
            Rprint( "***", "Not-update set: Don't even copy data to git." )
        else:
            LOG_TASK( "Syncdir", src.wsDir, "->", trg.wsDir )
            for t in glob.glob( f"{trg.wsDir}/*" ):
                os.remove( t )
            for s in glob.glob( f"{src.wsDir}/*" ):
                os.link( s, os.path.join( trg.wsDir, os.path.basename( s ) ) )
            trg.git( "add", "-A" ).run()

        LOG_SEP()
        stat = StepStat( trg.extractStatChanges( f"origin/{trg.currentBranch}" ) )
        if stat.curVersion is None:
            # up-to-date or no new version
            stat.curVersion = trg.guessVersion
        self.stats.fromObs = stat
        stat.LOG( src )
        LOG_SEP()

    def checkSubmittStatus( self, prbranches ):
        for prbranch in prbranches:
            if prbranch in self.stats.prbranches:
                raise Exception( f"{self}: checkSubmittStatus {prbranch}: Have status already." )
            self.submittStatus( prbranch )

    def submittStatus( self, prbranch ):
        trg = self.trg
        trgbranch = self.trgbranch
        # - Check whether a PR is running or not
        # - Check whether a PR should be updated (prbranch differs from trgbranch)
        # trgbnanch <(next submitt)> origin/trgbnanch <(should be in sync)> origin/prbranch <(PR)> parent/prbranch
        LOG_TASK( "submittStatus", self.trg, trgbranch, "->", prbranch )

        trgAt = f"origin/{trgbranch}"
        oriAt = f"origin/{prbranch}"
        parAt = f"parent/{prbranch}"

        if trg.strictAncestor( oriAt, trgAt ):    # Exception if not <=
            ostat = StepStat( trg.extractStatChanges( oriAt, trgAt ) )
        else:
            ostat = StepStat()  # up-to-date
        ostat.LOG( self.trg, prbranch, "ORIGIN" )

        if trg.strictAncestor( parAt, oriAt ):    # Exception if not <=
            pstat = StepStat( trg.extractStatChanges( parAt, oriAt ) )
        else:
            pstat = StepStat()  # up-to-date
        pstat.LOG( self.trg, prbranch, "PR" )

        runningPR = self._haveOpenPR( prbranch )

        self.stats.prbranches[prbranch] = ( ostat, pstat, runningPR )
        Mprint( "###", self.trg, prbranch )
        return

    def _haveOpenPR( self, prbranch ):
        # Return any open PR from Gitea.USER to pool/prbranch (expecting 0 or 1).
        # This will determine whether a running PR is updated or a new PR is filed.
        # PRs from foreign users are not desired and reported on screen. But we don't care.
        trg = self.trg
        LOG_TASK( "haveOpenPRs", self.trg, prbranch )
        myOpen = []
        for pr in trg.getOpenPRs( prbranch ):
            mypr = pr["head_owner"] == trg.GITEAUSER and pr["head_repo"] == self.pkg and pr["head_branch"] == prbranch
            if mypr:
                Gprint( pr["id"], pr["head_branch"], pr["updated_at"], pr["title"] )
                myOpen.append( pr["id"] )
            else:
                stag = f'{pr["head_owner"]}/{pr["head_repo"]}:{pr["head_branch"]}'
                Rprint( pr["id"], stag, pr["updated_at"], pr["title"] )
        if len(myOpen) > 1:
            Rprint( "***", "Multiple own PRs open:", myOpen )
        return myOpen



    def setFateFromStats( self ):
        self.fate = self.Fate( self.stats )

    def summarizeFate( self ):
        somethingToDO = False
        # on the fly check unprocessed parent branches
        knownBranches = set( m[1] for m in self.trg.git( "branch", "-r" ).stdout( stdout="^\s*parent/([^ ]*)$", quiet=True ).byMatch() )
        sawBranches   = set( ('factory',) )    # strip it

        self.stats.fromObs.LOG( self.src )
        toVersion = self.fate.toVersion

        for prbranch in self.fate.prbranches:
            updateOrigin, needPR, havePR, fromVersion = self.fate.prbranches[prbranch]
            runningPR = self.stats.runningPR( prbranch )

            if updateOrigin:   # update implies needPR
                tag = f"UPDATE_ORIGIN {'(pr_is_running)' if havePR else 'and FILE_NEW_PR'}"
                LOGprint = Mprint
                somethingToDO = True
            elif needPR:        # no update but need running PR
                tag = 'is fine! (pr_is_running)' if havePR else 'FILE_NEW_PR'
                LOGprint = Bprint if havePR else Mprint
                if not havePR: somethingToDO = True
            else:               # all fine
                tag = 'is fine!'
                LOGprint = Bprint

            oldv = f"({fromVersion})" if fromVersion != toVersion else ""
            runpr = f"{runningPR}" if runningPR else ""
            LOGprint( f"    - {str(self.trg):20} : {prbranch:10} : {tag:30} {toVersion:>9} {oldv} {runpr}" )
            sawBranches.add( prbranch )

        missingBranches = knownBranches - sawBranches
        Cprint( "   ", missingBranches )
        return somethingToDO

    def submitFate( self ):
        comitMsg = None
        if self.fate.commitFromObs:
            comitMsg = self.src.getRevisionInfo()
            LOG_STEP( "COMMIT_FROM_OBS", comitMsg )
            self.trg.git( "commit", "-m", comitMsg ).run()
            self.trg.git( "push", "origin" ).run()

        # beware: we change the local checkout here
        for prbranch in self.fate.prbranches:
            updateOrigin, needPR, havePR, fromVersion = self.fate.prbranches[prbranch]

            if updateOrigin:
                LOG_STEP( "UPDATE_ORIGIN", self.pkg, prbranch )
                self.trg.assertCleanBranch( prbranch, forceAt=self.trgbranch )
                self.trg.git( "push", "origin" ).run()

            if needPR:
                if havePR and not updateOrigin:
                    continue    # nothing to amend

                if comitMsg is None: comitMsg = self.src.getRevisionInfo()
                title = f"Update to {self.src} {self.fate.toVersion}"
                descr = comitMsg
                if not havePR:
                    LOG_STEP( "FILE_NEW_PR", self.pkg, prbranch )
                    self.trg.fileNewPr( prbranch, title=title, description=descr )
                elif updateOrigin:
                    mypr = self.stats.runningPR( prbranch )[0]
                    LOG_STEP( "Update running PR", mypr, prbranch )
                    self.trg.updatePR( mypr, title=title, description=descr )

