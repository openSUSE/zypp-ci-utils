import os, re, select, subprocess
from .cout import *

#======================================================================
def assertdir( path ):
    if not os.path.isdir( path ):
        if os.path.exists( path ):
            raise NotADirectoryError( f"assertdir: not a directory: {path}")
        os.makedirs( path )

def pathjoin( root, sub ):
    sub = sub.strip('/')    # os.path.join does not like leading "/"
    if not sub:
        return root
    return os.path.join( root, sub )

#======================================================================
class Cmd:
    #======================================================================
    # Run commands kwargs:
    # verbose = 0           : cls.verbosity as default (quiet=1 short for verbose=Cmd.QUIET)
    # failok = False        : Throw if return code is not 0
    # stdout/stderr = None  : Passing a regex rather than True will capture matching lines only.
    # interacive = False    : Force stdout/stderr=None and don't capture. Command may launch vi.
    # cwd                   : Set CWD for command
    #
    # ==> Returns a Result object
    #
    # Use like:
    #  result = Cmd("ls","-l").run()
    #  output = result.stdout
    # or:
    #  output = Cmd("ls","-l").stdout( stdout='^d' )
    #======================================================================
    QUIET   = 0
    STDOUT  = 1
    STDERR  = 2
    CMD     = 4
    SILENT  = STDERR|CMD
    VERBOSE = STDOUT|STDERR|CMD

    verbosity = VERBOSE

    #======================================================================
    class Capture:
        # Capture (opt. pre filter) lines passed to take.
        #
        # Pre filter: Passing a rx on construction will capture matching lines
        # (and their re.Match) only.
        #
        # Post filter: Retrieval functions supporting 'rx=None' as argument
        # will apply this additional filter to the captured lines.
        #
        def __init__( self, rx=None ):
            # rx: A regex string to pre filter, otherwise capture all
            if type(rx) is str:
                self._take = self._takeFilter
                self._cap = []  # the captured lines
                self._rx = re.compile( rx )
                self._rm = []   # the match objects
            else:
                self._take = self._takeAll
                self._cap = []  # the captured lines

        def __bool__( self ):   # at least one line was captured
            return bool(self._cap)

        def __len__( self ):
            return len(self._cap)

        def __getitem__( self, idx ):
            return self._cap[idx]


        def take( self, line ): # capture line (opt. pre filtering)
            self._take( line )
        def _takeAll( self, line ):
            self._cap.append( line )
        def _takeFilter( self, line ):
            match = self._rx.search( line )
            if match:
                self._cap.append( line )
                self._rm.append( match )


        def asString( self, rx=None ):    # NL separated lines (opt. post filtered)
            return "\n".join( self.byLine( rx ) )

        def byLine( self, rx=None ):    # Iterate line by line (opt. post filtered)
            if len(self._cap):
                if rx is None:
                    for l in self._cap:
                        yield l
                else:
                    rx = re.compile( rx )
                    for l in self._cap:
                        if rx.search( l ):
                            yield l

        def byMatch( self, rx=None ): # Iterate re.Matches (pre filter matches if rx is None, throws if no pre filter)
            if len(self._cap):
                if rx is None:  # pre filter re.Matches
                    for m in self._rm:
                        yield m
                else:           # post filter matches
                    rx = re.compile( rx )
                    for l in self._cap:
                        m = rx.search( l )
                        if m:
                            yield m


        def theLine( self, rx=None, *, missingOk=False ):    # Expect 1 captured/filtered line - throw if not
            ret = None
            for l in self.byLine( rx ):
                if ret is None:
                    ret = l
                    continue
                raise Exception( "theLine: More than 1 match" )
            if ret is None and not missingOk:
                raise Exception( "theLine: No match" )
            return ret

        def theMatch( self, rx=None, *, missingOk=False ):   # Expect 1 captured match/filtered - throw if not
            ret = None
            for l in self.byMatch( rx ):
                if ret is None:
                    ret = l
                    continue
                raise Exception( "theMatch: More than 1 match" )
            if ret is None and not missingOk:
                raise Exception( "theMatch: No match" )
            return ret


    #======================================================================
    class Result:
        def __init__( self, returncode, stdout, stderr ):
            self._returncode = returncode
            self._stdout = stdout   # Capture
            self._stderr = stderr   # Capture

        def __bool__( self ):
            return self._returncode == 0

        @property
        def returncode( self ):
            return self._returncode

        @property
        def stdout( self, rx=None ):    # Capture
            return self._stdout

        @property
        def stderr( self ):             # Capture
            return self._stderr

        def __str__( self ):
            return f"==> {self._returncode}"

    #======================================================================
    def __init__( self, *args ):
        self._args = args
        self._executedonce = False

    def __del__( self ):
        if not self._executedonce:
            Rprint( "NEVER RUN:", *self._args )

    def run( self, **kwargs ):  # -> Result or Exception
        return self._execute( **kwargs )

    def tryrun( self, **kwargs ): # -> Result (failok=True)
        if "failok" not in kwargs:
            kwargs["failok"] = True
        return self._execute( **kwargs )

    def stdout( self, **kwargs ): # Capture and return stdout
        if "stdout" not in kwargs:
            kwargs["stdout"] = True
        return self._execute( **kwargs ).stdout

    #======================================================================
    @property
    def _cmd( self ):
        return self._args

    def _execute( self, **kwargs ):
        if "verbose" not in kwargs:
            kwargs["verbose"] = self.verbosity
        self._executedonce = True
        return self._doexecute( *self._cmd, **kwargs )

    #======================================================================
    @classmethod
    def _doexecute( cls, *args, verbose=0, failok=False, stdout=None, stderr=None, interactive=False, cwd=None, quiet=False ):
        if not args: raise Exception( "NULL command" )
        if quiet: verbose=0
        if interactive: stdout=stderr=None

        proc = subprocess.Popen( args, bufsize=1, universal_newlines=True,
                                stdout=(None if interactive else subprocess.PIPE),
                                stderr=(None if interactive else subprocess.PIPE), cwd=cwd )
        if verbose & cls.CMD: print( "...", *args )
        stdout = cls.Capture( stdout ) if stdout else None
        stderr = cls.Capture( stderr ) if stderr else None

        if not interactive:
            reads = [ proc.stdout.fileno(), proc.stderr.fileno() ]
            os.set_blocking( reads[0], False )
            os.set_blocking( reads[1], False )
            while reads:
                if proc.poll() is None:
                    try:
                        ready = select.select( reads, [], [] )
                    except select.error as v:
                        if v[0] == errno.EINTR:
                            continue
                        raise
                else:
                    ready = [ reads ]
                    reads = None

                tag = "   "
                ol = ''     # collect not NL teminated reads
                el = ''     # -"-
                for fd in ready[0]:
                    if fd == proc.stdout.fileno():
                        for line in cls._readByLine( proc.stdout ):
                            ol += line
                            if line[-1] != "\n":
                                continue
                            line = ol.rstrip("\n")
                            ol = ''
                            if verbose & cls.STDOUT: Cprint( tag, '>', line )
                            if stdout is not None: stdout.take( line )
                    if fd == proc.stderr.fileno():
                        for line in cls._readByLine( proc.stderr ):
                            el += line
                            if line[-1] != "\n":
                                continue
                            line = el.rstrip("\n")
                            el = ''
                            if verbose & cls.STDERR: Mprint( tag, '*', line )
                            if stderr is not None: stderr.take( line )

        proc.wait()
        result = cls.Result( proc.returncode, stdout, stderr )
        if not result:
            if verbose: Rprint( result )
            if not failok: raise Exception( (result, args) )
        return result

    @staticmethod
    def _readByLine( stream ):  # expects a non-blocking text stream
        while True:
            line = stream.readline()
            if line:
                yield line
            else:
                break

#======================================================================
class CmdWorkspace:
    '''
        Simple workspace helper associated with a (Cmd) type.The cmdtype
        name determines the name of the workspace root directory. The
        optional wsPath a subdirectory within the workspace.

            class Obs( Cmd ):
                ...
            class Ibs( Cmd ):
                ...
            class Prj( CmdWorkspace ):
                def __init__( self, obs, prj ):
                    super().__init__( obs, prj )
                ...
            class Pkg( CmdWorkspace ):
                def __init__( self, obs, prj, pkg ):
                    super().__init__( obs, os.path.join( prj, pkg ) )
                ...
            pkg = Pkg( Obs, "zypp:Head", "libzypp" )
            # has wsRoot: Obs
            # has wsDir:  Obs/zypp:Head/libzypp
    '''
    def __init__( self, cmdtype, wsPath="" ):
        self.cmdtype = cmdtype                   # self.cmdtype( *args ).run( cwd=.. )
        self.wsRoot  = self.cmdtype.__name__     # workspace root named after the command type name
        self.wsPath  = wsPath                    # opt. subpath below wsRoot for this instance
        self.wsDir   = pathjoin( self.wsRoot, self.wsPath ) # wsRoot / wsPath

    def assertWsDir( self ):
        assertdir( self.wsDir )

    @property
    def TAG( self ):
        return f"### {self}:"
