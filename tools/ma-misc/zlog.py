#! /usr/bin/python3
import sys, os, re, time, stat, select
import sys, traceback

from PyQt6.QtCore    import *
from PyQt6.QtGui     import *
from PyQt6.QtWidgets import *

#======================================================================
class WorkerSignals( QObject ):
    ''' Signals available from a running worker thread. '''
    started     = pyqtSignal()          # No data
    result      = pyqtSignal(object)    # data returned from processing, anything
    error       = pyqtSignal(tuple)     # ( exctype, value, traceback.format_exc() )
    finished    = pyqtSignal()          # No data

    progress    = pyqtSignal(int)       # workerCallbacks[0]: indicating % progress
    data        = pyqtSignal(object)    # workerCallbacks[1]: data produced while processing, anything

    def workerCallbacks( self ):
        return ( self.progress, self.data )

class Worker( QRunnable ):
    '''
    Worker thread.

    :param callback: The function callback to run on this worker thread. Supplied
                     args and kwargs will be passed through to the runner.
    :param args: Arguments to pass to the callback function
    :param kwargs: Keywords to pass to the callback function

    def __init__( self ):
        self.threadpool = QThreadPool()
        print( "Multithreading with maximum %d threads" % self.threadpool.maxThreadCount() )

    def start( self, argv ):
        worker = Worker( self.execute_this_fn, "arg" ) # Any other args, kwargs are passed to the run function
        worker.signals.result.connect( self.print_output )
        worker.signals.finished.connect( self.thread_complete )
        worker.signals.progress.connect( self.progress_fn )
        self.threadpool.start( worker )
        #or QThreadPool.globalInstance()...

    def execute_this_fn( self, arg, workerCallbacks ):
        return "Done."
    '''
    AbortAll = None

    def __init__( self, fn, *args, workerSignals=None, **kwargs ):
        super().__init__()
        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = workerSignals if workerSignals is not None else WorkerSignals()
        self.kwargs['workerCallbacks'] = self.signals.workerCallbacks()

    @pyqtSlot()
    def run( self ):
        '''
        Initialise the runner function with passed args, kwargs.
        '''
        self.signals.started.emit()  # Go...
        try:
            result = self.fn( *self.args, **self.kwargs )
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit( (exctype, value, traceback.format_exc()) )
        else:
            self.signals.result.emit( result )  # Return the result of the processing
        finally:
            self.signals.finished.emit()  # Done


    @classmethod
    def abortAll( cls ):
        QThreadPool.globalInstance().clear()
        cls.AbortAll = True
        return QThreadPool.globalInstance().waitForDone(1000)
#======================================================================

class Ansi:
    Black         = (30, 40)
    Red           = (31, 41)
    Green         = (32, 42)
    Yellow        = (33, 43)
    Blue          = (34, 44)
    Magenta       = (35, 45)
    Cyan          = (36, 46)
    White         = (37, 47)
    BrightBlack   = (90,100)
    BrightRed     = (91,101)
    BrightGreen   = (92,102)
    BrightYellow  = (93,103)
    BrightBlue    = (94,104)
    BrightMagenta = (95,105)
    BrightCyan    = (96,106)
    BrightWhite   = (97,107)

    OFF = "\033[0m"
    BLK = "\033[0;30m"
    GRY = "\033[0;90m"
    WHT = "\033[0;37m"
    WWW = "\033[0;97m"
    R   = "\033[0;31m"
    G   = "\033[0;32m"
    B   = "\033[0;34m"
    C   = "\033[0;36m"
    M   = "\033[0;35m"
    Y   = "\033[0;33m"
    HDR = "\033[0;42m"

    DBG = "\033[0;36;40m"

def DBG( *args, **kwargs ):
    print( Ansi.DBG, end='', **kwargs )
    print( *args, end='', **kwargs )
    print( Ansi.OFF, **kwargs )

#======================================================================
class LogLine( object ):
    ''' 2020-04-14 10:58:37 <1> hobbes(1198) [zypper++] main.cc(main):97 {T:Zypp-main} ===== Hi, me zypper 1.14.36 '''
    rxDate   = r'(?P<dateFld>[0-9]{4}-[0-9]{2}-[0-9]{2})'                             # 2020-04-14
    rxTime   = r'(?P<timeFld>[0-9]{2}:[0-9]{2}:[0-9]{2})'                             # 10:58:37
    rxLevel  = r'(?P<levelFld><(?P<level>[0-9]+)>)'                                   # <1>               (0 mapped to -1 (hide YAST DBG))
    rxHost   = r'(?P<hostFld>(?P<host>[^(]*)\((?P<pid>[0-9]+)\))'                     # hobbes(1198)
    rxGroup  = r'(?P<groupFld>\[(?P<group>[^]+]*)(?P<zlv>\+\+)?\])'                   # [zypper++]        (trailing ++ mapped to level 0)
    rxFile   = r'(?P<fileFld>(?P<file>[^(:]*)(\((?P<fnc>[^ ]*)\))?:(?P<lne>[0-9]+))'  # main.cc(main):97
    rxThread = r'(?P<threadFld>{T:(?P<thread>[^}]+)})'                                # {T:Zypp-main}
    rxText   = r'(?P<textFld>.*)'                                                     # ===== Hi, me zypper 1.14.36
    rxData   = re.compile( '^%s +%s +%s +%s +%s +%s(?: +%s)? +%s$' % ( rxDate, rxTime, rxLevel, rxHost, rxGroup, rxFile, rxThread, rxText ) )
    rxDataGroups = re.findall( r"\?P<([^>]*)>", rxData.pattern )

    def __init__( self, rxDataMatch ):
        super().__init__()
        self._l = rxDataMatch.group()
        self._g = { g:rxDataMatch.span(g) for g in self.rxDataGroups }

        # <1> ... [zypper++] (trailing ++ mapped to level 0)
        if self.hasGroup( 'zlv' ):
            self['zlv'] = ""
            self['level'] = "0"

        # Command start headlines
        if self['file'] == "main.cc" and self['fnc'] == "main" and self['textFld'].startswith( "=====" ):
            if self['textFld'].startswith( "===== Hi, me zypper" ):
                self._style = "Hs"
            else:
                self._style = "H"
        elif self['file'] == "threaddata.cc" and self['fnc'] == "ensureDispatcher":
            self._style = f"{self['level']}s"
        elif self['file'] == "genericfrontend.cc" and self['textFld'].startswith( "Launched YaST2 component" ):
            self._style = "Hs"
        elif self['file'] == "bin/y2start" and self['textFld'].startswith( "y2base called with" ):
            self._style = "Hs"

    def append( self, line ):
        self._l += "\n"
        self._l += line.rstrip('\n')

    @property
    def levelStyle( self ):
        return self._style[:1] if '_style' in self.__dict__ else self['level']

    @property
    def isCmdStart( self ):
        return '_style' in self.__dict__ and self._style[-1:] == "s"

    def hasGroup( self, group ):
        return self._g[group][0] != -1

    def __getitem__( self, group ):
        beg,end = self._g[group]  # (-1,-1) if not existing match
        if beg == -1:
            return # group does not exist
        return self._l[beg:end]

    def __setitem__( self, group, val ):
        beg,end = self._g[group]  # (-1,-1) if not existing match
        if beg == -1:
            return # group does not exist
        self._l = f"{self._l[:beg]}{val}{self._l[end:]}"
        diff = len(val)-(end-beg)
        if diff:    # adjust spans
            for g in self._g:
                b,e = self._g[g]
                if b == -1: continue
                if e <= beg: continue
                if b > beg: b += diff
                if e > beg: e += diff
                self._g[g] = (b,e)

    def __str__( self ):
        return f"{self._l}"

#======================================================================
class LogLineParser( Worker ):
    """ """
    def __init__( self, argv, **kwargs ):
        if type(argv) is str: argv = [ argv ]
        super().__init__( self._workhorse, argv, **kwargs )

    @classmethod
    def _getLines( cls, argv ):
        for arg in argv:
            if arg == "-":
                DBG( "===", "STDIN" )
                for line in sys.stdin:
                    yield line
            else:
                DBG( "===", arg )
                with open( arg, 'r' ) as file:
                    for line in file:
                        yield line

    @classmethod
    def _sendLogLine( cls, logline, workerCallbacks ):
        if logline is not None:
            workerCallbacks[1].emit( logline )

    @classmethod
    def _workhorse( cls, argv, workerCallbacks, **kwargs ):
        logline = None
        for line in cls._getLines( argv ):
            m = re.match( LogLine.rxData, line )
            if m:
                cls._sendLogLine( logline, workerCallbacks )
                logline = LogLine( m )
            elif logline is not None:
                logline.append( line )
            else:
                pass #print( line.rstrip('\n') )    # leading garbage
        cls._sendLogLine( logline, workerCallbacks )

#======================================================================
class LogLineFormater( object ):
    """ """
    _levelcolor = {# ( normal, inverted )
        None: ( Ansi.GRY, Ansi.WWW.replace("m",";100m") ),  # Fallback or excessive
        "0" : ( Ansi.C,   Ansi.C.replace("m",";100m") ),
        "1" : ( Ansi.BLK, Ansi.WHT.replace("m",";100m") ),
        "2" : ( Ansi.Y,   Ansi.Y.replace("m",";100m") ),
        "3" : ( Ansi.R,   Ansi.R.replace("m",";100m") ),
        "4" : ( Ansi.M,   Ansi.M.replace("m",";100m") ),
        "5" : ( Ansi.G,   Ansi.G.replace("m",";100m") ),
        "6" : ( Ansi.B,   Ansi.B.replace("m",";100m") ),
        "H" : ( Ansi.HDR, Ansi.HDR ),  # Command headline
        }

    def __init__( self ):
        super().__init__()
        self._topc = None

    def _getLevelColor( self, level, style=0 ):
        return self._levelcolor.get( level, self._levelcolor[None] )[style]

    def _print( self, logline ):
        style=0
        if logline.isCmdStart or self._topc is None:
            self._topc = logline['pid']
        elif logline['pid'] != self._topc:
            style = 1
        ansi = self._getLevelColor( logline.levelStyle, style )

        logstr = str(logline)
        # TODO: highlight matches
        # workaround less resetting ansi at NL:
        print( ansi, logstr.replace( "\n", f"\n{ansi}" ), sep='', end=f'\n{Ansi.OFF}' )

    def print( self, loglines ):
        self._print( loglines ) if type(loglines) == LogLine else [ self._print( c ) for c in loglines ]

#======================================================================
class LogCmd( QObject ):
    """ """
    datachanged = pyqtSignal(object)    # indicate data were added/changed since last flush

    def __init__( self ):
        super().__init__()

    def init( self, logline, cidx ):
        if '_line' in self.__dict__:
            raise Exception( "Command already started" )
        self.CIDX = cidx
        self._line = logline
        self._last = logline
        self._z = {}
        self._extract = [ self._evers, self._elvers, self._ecmd, self._ero, self._eexit, ]
        self.process( logline )
        self.needtoflush = True

    @property
    def line( self ):
        return self._line

    @property
    def last( self ):
        return self._last

    @property
    def pid( self ):
        return self._line['pid']


    @property
    def needtoflush( self ):
        try:
            return self._needtoflush
        except AttributeError:
            self._needtoflush = False
            return self._needtoflush
    @needtoflush.setter
    def needtoflush( self, val ):
        if val != self.needtoflush:
            self._needtoflush = val
            if val:
                self.datachanged.emit( self )

    def _zhas( self, key ):
        return key in self._z

    def _zget( self, key, default="?" ):
        return self._z[key] if self._zhas( key ) else default

    def _zset( self, key, val ):
        if not self._zhas( key ) or self._z[key] != val:
            self._z[key] = val
            self.needtoflush = True


    @property
    def cmd( self ):
        return self._zget( 'cmd' )

    @property
    def cmdStart( self ):
        if self._zhas( 'cmd' ):
            return f"{self._line['dateFld']} {self._line['timeFld']}"
        return "????-??-?? ??:??:??"

    @property
    def cmdLast( self ):
        return f"           {self._last['timeFld']}"

    @property
    def vers( self ):
        return self._zget( 'vers' )

    @property
    def lvers( self ):
        return self._zget( 'lvers' )

    @property
    def ro( self ):
        return self._zget( 'ro', False )

    @property
    def exit( self ):
        #  ... not yet finished
        #  ??? finished exit code unknown
        #  nnn exit code
        #      0
        return self._zget( 'exit', '...' )

    @property
    def exited( self ):
        return self._zhas( 'exit' )

    def flush( self ):
        LogCmdFormater().print( self )
        self.needtoflush = False


    def _evers( self, logline ):
        m = re.match( "===== Hi, me zypper (.*)", logline['textFld'] )
        if m:
            self._zset( 'vers', m[1] )
            return True

    def _elvers( self, logline ):
        if logline['fnc'] == "ZConfig" and logline['textFld'].startswith( "libzypp:" ):
             self._zset( 'lvers', logline['textFld'][9:] )
             return True

    def _ecmd( self, logline ):
        if logline.levelStyle == "H" and re.match( "===== '.*' =====", logline['textFld'] ):
            m = re.match( "===== '(.*)' =====", logline['textFld'] )
            if m:
                self._zset( 'cmd', m[1].replace( "' '", " " ) )
                return True

    def _ero( self, logline ):
        if logline['fnc'] == "IWantIt" and logline['textFld'].startswith( "ZYPP_READONLY promised" ):
            self._zset( 'ro', True )
            return True

    def _eexit( self, logline ):
        if logline['fnc'] == "~Bye":
            m = re.match( r"===== Exiting main\(([0-9]*)\)", logline['textFld'] )
            self._zset( 'exit', m[1] if m else "???" )
            return True


    def process( self, logline ):
        logline.CIDX = self.CIDX
        self._last = logline
        #print( "###", self._zget( 'lvers' ), logline )

        if len(self._extract):
            self._extract = [ex for ex in self._extract if not ex( logline )]

        #print( len(self._extract), self._extract )

#======================================================================
class LogCmdFormater( object ):
    """ """
    def __init__( self ):
        super().__init__()

    def _cstr( self, ansi, txt ):
        return f"{ansi}{txt}{Ansi.OFF}"

    def _print( self, cmd ):
        ff = '_ff' not in cmd.__dict__  # first flush
        if ff: cmd._ff = True

        t = cmd.cmdStart if ff else cmd.cmdLast
        p = f"{cmd.pid:>6}"
        v = f"{cmd.vers if ff else ':':>8}"
        lv = f"{cmd.lvers if ff else ':':>8}"
        exit = cmd.exit
        if exit == "0": exit = ""
        x = f"{exit:>3}"
        r = "r" if cmd.ro else " "
        c = cmd.cmd if ff else "---" if cmd.exited else "..."

        if ff:
            if exit == "...":
                p = self._cstr( Ansi.M, p )
                x = self._cstr( Ansi.M, x )
                c = self._cstr( Ansi.M, c )
            elif len(exit) == 1:
                x = self._cstr( Ansi.R, x )
                c = self._cstr( Ansi.R, c )
            elif len(exit) > 1:
                x = self._cstr( Ansi.B, x )
                c = self._cstr( Ansi.B, c )
        else:
            p = self._cstr( Ansi.M, p )
            v = self._cstr( Ansi.M, v )
            if len(exit) == 1:
                x = self._cstr( Ansi.R, x )
                c = self._cstr( Ansi.R, c )
            elif len(exit) > 1:
                x = self._cstr( Ansi.B, x )
                c = self._cstr( Ansi.B, c )
            else:
                x = self._cstr( Ansi.M, x )
                c = self._cstr( Ansi.M, c )

        print( t, p, v, lv, x, r, c )


    def print( self, cmds ):
        if type(cmds) == LogCmd:
            self._print( cmds )
        elif True:
            [ self._print( c ) for c in cmds ]

#======================================================================
class LogData( QObject ):
    """ """
    def __init__( self ):
        super().__init__()
        self._cmds = []     # Commands
        self._ncmds = 0     # CIDX [0,1,...] for commands started in the log
        self._ocmds = 0     # CIDX [-1,-2,...] for command artefacts started before
        self._lines = 0     # LIDX for LogLines
        self._topCmd = None # cache last new command
        self._toflush = None


    def _makeCommand( self, logline, cidx ):
        cmd = LogCmd()
        cmd.datachanged.connect( self.flush )
        cmd.init( logline, cidx )
        return cmd

    def _addNewCommand( self, logline ):
        cidx = self._ncmds
        self._ncmds += 1
        cmd = self._topCmd = self._makeCommand( logline, cidx )
        self._cmds.append( cmd )

    def _addOldCommand( self, logline ):
        self._ocmds += 1
        cidx = -self._ocmds
        cmd = self._makeCommand( logline, cidx )
        self._cmds.insert( 0, cmd )

    def process( self, logline ):
        # add to lines
        logline.LIDX = self._lines
        self._lines += 1
        # sort into cmds
        if logline.isCmdStart and ( self._topCmd is None or self._topCmd.pid != logline['pid'] ):
            self._addNewCommand( logline )
        elif self._topCmd is None:
            self._addOldCommand( logline )
        else:
            pid = logline['pid']
            if self._topCmd.pid == pid:
                self._topCmd.process( logline )
            else:
                # Nested commands
                for i in reversed(range(len(self._cmds)-1)):
                    c = self._cmds[i]
                    if c.pid == pid:
                        c.process( logline )
                        break
                else:
                    # something from even before the log started
                    self._addOldCommand( logline )
        #DBG( f"({logline.LIDX}.{logline.CIDX})", str(logline)[:50] )

    @pyqtSlot(object)
    def flush( self, cmd ):
        # allow a command to continue collecting until another one wants to flush too
        if self._toflush is not None:
            self._toflush.flush()
        self._toflush = cmd

    def __len__( self ):
        return len(self._lines)

#======================================================================
class ApplicationMain( QApplication ):
    """ PyQT in case we want signals """

    def __init__( self ):
        super().__init__( sys.argv )
        self._ld = LogData()            # For command table
        self._lp = LogLineFormater()    # For cat log lines
        self._lpPids = []

    @pyqtSlot(LogLine)
    def processCmds( self, logline ):
        self._ld.process( logline )

    @pyqtSlot(LogLine)
    def processLines( self, logline ):
        if len(self._lpPids) == 0 or logline['pid'] in self._lpPids:
            self._lp.print( logline )

    def postprocess( self ):
        self._ld.flush( None )          # flush any pending entries

    @pyqtSlot(object)
    def start( self, argv ):
        logs = []
        pids = self._lpPids = []
        process = self.processCmds

        for arg in argv:
            if arg == "0":
                process = self.processLines # cat all PIDs
            elif re.fullmatch( "[0-9]+", arg ):
                pids.append( arg )
            else:
                logs.append( arg )

        if len(logs) == 0:
            logs.append( "z.log" if os.path.exists( "z.log" ) else "/var/log/zypper.log" )

        if len(pids):
            process = self.processLines

        lp = LogLineParser( logs )
        lp.signals.data.connect( process )
        lp.signals.finished.connect( self.finish )
        QThreadPool.globalInstance().start( lp )

    @pyqtSlot()
    def finish( self ):
        self.postprocess()
        QThreadPool.globalInstance().clear()
        QThreadPool.globalInstance().waitForDone()
        self.quit()

#======================================================================
def main():
    app = ApplicationMain()
    QTimer.singleShot( 0, lambda : app.start( sys.argv[1:] ) )
    sys.exit( app.exec() )

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print( "OOps:", e )
