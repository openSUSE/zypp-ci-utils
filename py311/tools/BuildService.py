from .Cmd import *

#======================================================================
class BuildService( Cmd ):
    #verbosity = Cmd.SILENT
    _bscmd = ("osc",)  # the default

    @property
    def _cmd( self ):
        return ( *self._bscmd, *self._args )

    @classmethod
    def Prj( cls, prj ):        # project factory
        return _Prj( cls, prj )

    @classmethod
    def Pkg( cls, prj, pkg ):   # package factory
        return _Pkg( cls, prj, pkg )

#======================================================================
class _BSWorkspace( CmdWorkspace ):
    def __init__( self, cmdtype, wsPath ):
        if type(cmdtype) is not type or not issubclass( cmdtype, BuildService ):
            raise TypeError( f"{type(self).__name__}: BAD {type(cmdtype)} for cmdtype" )
        super().__init__( cmdtype, wsPath )

    @property
    def osc( self ):            # osc: some commands may need cwd=self.wsDir
        return self.cmdtype

    @property
    def Factory( self ):
        return self.cmdtype

    @property
    def wsName( self ):
        return self.cmdtype.__name__

#======================================================================
class _Prj( _BSWorkspace ):
    def __init__( self, cmdtype, prj ):
        if type(prj) is not str:
            raise TypeError( f"{type(self).__name__}: BAD {type(prj)} prj" )
        super().__init__( cmdtype, prj )
        self.prj = prj  # str

    def Pkg( self, pkg ):
        return self.Factory.Pkg( self.prj, pkg )

    def suggestGitBranchName( self ):
        name = f"{self.wsName}-{self.prj}"
        name = name.replace( ':', '-' )
        return name

    def __str__( self ):
        return f"{self.wsName}:/{self.prj}"

#======================================================================
class _Pkg( _BSWorkspace ):
    def __init__( self, cmdtype, prj, pkg ):
        if type(prj) is not str or not prj:
            raise TypeError( f"{type(self).__name__}: BAD {type(prj)} prj" )
        if type(pkg) is not str or not pkg:
            raise TypeError( f"{type(self).__name__}: BAD {type(pkg)} pkg" )
        super().__init__( cmdtype, os.path.join( prj, pkg ) )
        self.prj = prj  # str
        self.pkg = pkg  # str

    def __str__( self ):
        return f"{self.wsName}:/{self.prj}/{self.pkg}"

    def assertCheckout( self ):
        if not os.path.isdir( os.path.join( self.wsDir, ".osc" ) ):
            Bprint( self.TAG, "assertCheckout" )
            self.assertWsDir()
            self.osc( "co", self.prj, self.pkg ).run( cwd=self.wsRoot )

    def updateCheckout( self, *, taintedOk=False ):
        self.assertCheckout()
        Bprint( self.TAG, "updateCheckout" )
        self.osc( "up" ).run( cwd=self.wsDir )
        out = self.osc( "status" ).stdout( cwd=self.wsDir )
        if out: # clean if no output from "status"
            if taintedOk:
                Mprint( "!!!", "Not clean but taintedOk!" )
            else:
                raise Exception( f"{self}: Checkout not clean." )


    def getRevisionInfo( self ):
        out = self.osc( "info" ).stdout( stdout="^Revision: ([0-9]+)", cwd=self.wsDir, quiet=True )
        rev = out.theMatch()[1]
        out = self.osc( "log", "--csv", "-r", rev ).stdout( cwd=self.wsDir, quiet=True )
        # "3047","zypp-team","2026-07-06 12:58:34","130edd0c5c7f585f79cc6fd83fc3169b","gitrev 8c9d169ff (...), 2026-07-06)",""
        return out.theLine().split( '","' )[4]



