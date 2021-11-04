#======================================================================
import sys
#======================================================================

def _cwrite( stream, color, term, *args ):
    stream.write( color )
    for arg in args: stream.write( arg )
    stream.write( _DEF )
    if term: stream.write( "\n" )

#======================================================================

_DEF	= "\033[0m"
_RED	= "\033[31m"
_BLU	= "\033[34m"
_GRE	= "\033[32m"
_CYA	= "\033[36m"
_MAG	= "\033[35m"
_WHI	= "\033[37m"
_BLA	= "\033[30m"

def wOUT( color, *args ):  _cwrite( sys.stdout, color, False, *args )
def pOUT( color, *args ):  _cwrite( sys.stdout, color, True,  *args )
def eOUT( color, *args ):  _cwrite( sys.stderr, color, False, *args )
def peOUT( color, *args ): _cwrite( sys.stderr, color, True,  *args )

# (w)rite (no auto NL)
def wDEF( *args ): wOUT( _DEF, *args )
def wRED( *args ): wOUT( _RED, *args )
def wBLU( *args ): wOUT( _BLU, *args )
def wGRE( *args ): wOUT( _GRE, *args )
def wCYA( *args ): wOUT( _CYA, *args )
def wMAG( *args ): wOUT( _MAG, *args )
def wWHI( *args ): wOUT( _WHI, *args )
def wBLA( *args ): wOUT( _BLA, *args )

# (p)rint (auto NL)
def pwDEF( *args ): pwOUT( _DEF, *args )
def pwRED( *args ): pwOUT( _RED, *args )
def pwBLU( *args ): pwOUT( _BLU, *args )
def pwGRE( *args ): pwOUT( _GRE, *args )
def pwCYA( *args ): pwOUT( _CYA, *args )
def pwMAG( *args ): pwOUT( _MAG, *args )
def pwWHI( *args ): pwOUT( _WHI, *args )
def pwBLA( *args ): pwOUT( _BLA, *args )

# write to strerr
def eDEF( *args ): eOUT( _DEF, *args )
def eRED( *args ): eOUT( _RED, *args )
def eBLU( *args ): eOUT( _BLU, *args )
def eGRE( *args ): eOUT( _GRE, *args )
def eCYA( *args ): eOUT( _CYA, *args )
def eMAG( *args ): eOUT( _MAG, *args )
def eWHI( *args ): eOUT( _WHI, *args )
def eBLA( *args ): eOUT( _BLA, *args )

# print to stderr
def peDEF( *args ): peOUT( _DEF, *args )
def peRED( *args ): peOUT( _RED, *args )
def peBLU( *args ): peOUT( _BLU, *args )
def peGRE( *args ): peOUT( _GRE, *args )
def peCYA( *args ): peOUT( _CYA, *args )
def peMAG( *args ): peOUT( _MAG, *args )
def peWHI( *args ): peOUT( _WHI, *args )
def peBLA( *args ): peOUT( _BLA, *args )

#======================================================================
