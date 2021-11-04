#======================================================================
import cout
import cmd
import re
#======================================================================

class Osc():

    @classmethod
    def cmd( cls, *args ):
        for line in cmd.run( cls._cmdstr(), *args ):
            yield line

    @classmethod
    def ls( cls, rx = None ):
        for line in cls.cmd( 'ls' ):
            if rx and not re.match( rx, line ): continue
            yield Prj( cls, line )

    @classmethod
    def prj( cls, prj ):
        return Prj( cls, prj )

    @classmethod
    def pkg( cls, prj, pkg ):
        return Pkg( Prj( cls, prj ), pkg )

    @classmethod
    def _cmdstr( cls ):
        return 'unknown'

    @classmethod
    def __str__( cls ):
        return cls._cmdstr()

#======================================================================

class Obs( Osc ):

    @classmethod
    def _cmdstr( cls ):
        return 'osc'

    @classmethod
    def __str__( cls ):
        return 'obs:/'

#======================================================================

class Ibs( Osc ):

    @classmethod
    def _cmdstr( cls ):
        return 'isc'

    @classmethod
    def __str__( cls ):
        return 'ibs:/'

#======================================================================

class Prj():

    def __init__( self, osc, name ):
        self._osc = osc
        self._name = name

    def osc( self ):
        return self._osc

    def name( self ):
        return self._name

    def ls( self, rx = None ):
        for line in self._osc.cmd( 'ls', self._name ):
            if rx and not re.match( rx, line ): continue
            yield Pkg( self, line )

    def pkg( self, name ):
        return Pkg( self, name )

    def __str__( self ):
        return self._name

#======================================================================

class Pkg():

    def __init__( self, prj, name  ):
        self._prj = prj
        self._name = name
        self._link = None
        self._version = None
        self.__content = None

    def osc( self ):
        return self._prj.osc()

    def prj( self ):
        return self._prj

    def name( self ):
        return self._name

    def ls( self, rx = None ):
        for line in self._content():
            if rx and not re.match( rx, line ): continue
            yield line

    def isLink( self ):
        if self.__content is None:
            self._content()	# adjusts _link
        return bool( self._link )

    def linkPrjName( self ):
        if self.isLink():
            return self._link[0]

    def linkPkgName( self ):
        if self.isLink():
            return self._link[1]

    def linkPkgVersion( self ):
        if self.isLink():
            return self._link[2]

    def linkPrj( self ):
        if self.isLink():
            return Prj( osc(), self._link[0] )

    def linkPkg( self ):
        if self.isLink():
            return Pkg( Prj( self.osc(), self._link[0] ), self._link[1] )

    def link( self ):
        return self.linkPkg()

    def version( self ):
        if self._version is None:
            for line in self._content():
                m = re.search( "-([^-]*)\\.tar", line )
                if ( m ):
                    self._version = m.group( 1 )
                    break
        return self._version

    def _content( self ):
        if self.__content is None:
            self.__content = list()
            for line in self.osc().cmd( 'ls', self._prj.name(), self._name ):
                if ( line[0] == '#'):
                    self._link = line.split(" ")[2:]
                    self.__content = list()	# reset on link: # -> zypp:SLE-11-SP3-Branch libzypp (latest)
                self.__content.append( line )
        return self.__content

    def __str__( self ):
        return self._name

#======================================================================
