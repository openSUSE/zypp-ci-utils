import sys, os, re
from .cout import *
from .Cmd import *
from .BuildService import *
from .Gitea import *
from .Gitea import *
from .SubmissionTask import *
#======================================================================
def checkWorkspaceMagic( magicfile ):
    # Prevent us from doing checkouts at arbitrary CWDs
    if not os.path.exists( magicfile ):
        raise Exception( f"Wrong CWD? No magic file '{magicfile}' in CWD." )

#======================================================================
# Our default BuildService instances
#
class Obs( BuildService ):
    _bscmd = ("osc",)   # the cmd to execute
    _usrname = "osc"    # a user friendly name for the above cmd (in messages e.g.)

class Ibs( BuildService ):
    _bscmd = ("isc",)    # if alias or ("osc","-A","https://api.suse.de")
    _usrname = "isc"

#======================================================================
# Our default Gitea instances
#
Gitea.USER = "nobody" # Owner of the forks

class GitObs( Gitea ):
    _bscmd = ("git-obs",)
    _usrname = "git-obs"

class GitIbs( Gitea ):
    _bscmd = ("git-ibs",)   # if alias or ("git-obs","-G","ibs") or similar
    _usrname = "git-ibs"
