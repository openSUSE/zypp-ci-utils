#======================================================================
import sys
#======================================================================

def _swrite( color, *args ):
  txt = None
  for arg in args:
    if txt is None:
      txt = color
    else:
      txt += ' '
    txt +=  str(arg)
  txt += DEF
  return txt

def _cwrite( stream, color, sep, nl, *args ):
  stream.write( color )
  for arg in args:
    stream.write( str(arg) )
    if sep: stream.write( sep )
  stream.write( DEF )
  if nl: stream.write( nl )

#======================================================================

DEF	= "\033[0m"
RED	= "\033[31m"
BLU	= "\033[34m"
GRE	= "\033[32m"
CYA	= "\033[36m"
MAG	= "\033[35m"
YEL	= "\033[33m"
WHI	= "\033[37m"
BLA	= "\033[30m"

# args ' 'joined to string
def sOUT( color, *args ): return _swrite( color, *args )

def sDEF( *args ): return sOUT( DEF, *args )
def sRED( *args ): return sOUT( RED, *args )
def sBLU( *args ): return sOUT( BLU, *args )
def sGRE( *args ): return sOUT( GRE, *args )
def sCYA( *args ): return sOUT( CYA, *args )
def sMAG( *args ): return sOUT( MAG, *args )
def sYEL( *args ): return sOUT( YEL, *args )
def sWHI( *args ): return sOUT( WHI, *args )
def sBLA( *args ): return sOUT( BLA, *args )


# args concatenated and written
def wOUT( color, *args ): _cwrite( sys.stdout, color, None, None, *args )
def eOUT( color, *args ): _cwrite( sys.stderr, color, None, None, *args )

def wDEF( *args ): wOUT( DEF, *args )
def wRED( *args ): wOUT( RED, *args )
def wBLU( *args ): wOUT( BLU, *args )
def wGRE( *args ): wOUT( GRE, *args )
def wCYA( *args ): wOUT( CYA, *args )
def wMAG( *args ): wOUT( MAG, *args )
def wYEL( *args ): wOUT( YEL, *args )
def wWHI( *args ): wOUT( WHI, *args )
def wBLA( *args ): wOUT( BLA, *args )

def eDEF( *args ): eOUT( DEF, *args )
def eRED( *args ): eOUT( RED, *args )
def eBLU( *args ): eOUT( BLU, *args )
def eGRE( *args ): eOUT( GRE, *args )
def eCYA( *args ): eOUT( CYA, *args )
def eMAG( *args ): eOUT( MAG, *args )
def eYEL( *args ): eOUT( YEL, *args )
def eWHI( *args ): eOUT( WHI, *args )
def eBLA( *args ): eOUT( BLA, *args )

# args concatenated and written + NL
def wlOUT( color, *args ): _cwrite( sys.stdout, color, None, '\n', *args )
def elOUT( color, *args ): _cwrite( sys.stderr, color, None, '\n', *args )

def wlDEF( *args ): wlOUT( DEF, *args )
def wlRED( *args ): wlOUT( RED, *args )
def wlBLU( *args ): wlOUT( BLU, *args )
def wlGRE( *args ): wlOUT( GRE, *args )
def wlCYA( *args ): wlOUT( CYA, *args )
def wlMAG( *args ): wlOUT( MAG, *args )
def wlYEL( *args ): wlOUT( YEL, *args )
def wlWHI( *args ): wlOUT( WHI, *args )
def wlBLA( *args ): wlOUT( BLA, *args )

def elDEF( *args ): elOUT( DEF, *args )
def elRED( *args ): elOUT( RED, *args )
def elBLU( *args ): elOUT( BLU, *args )
def elGRE( *args ): elOUT( GRE, *args )
def elCYA( *args ): elOUT( CYA, *args )
def elMAG( *args ): elOUT( MAG, *args )
def elYEL( *args ): elOUT( YEL, *args )
def elWHI( *args ): elOUT( WHI, *args )
def elBLA( *args ): elOUT( BLA, *args )

# args ' 'joined and written + NL
def wwOUT( color, *args ): _cwrite( sys.stdout, color, ' ', '\n', *args )
def ewOUT( color, *args ): _cwrite( sys.stderr, color, ' ', '\n', *args )

def wwDEF( *args ): wwOUT( DEF, *args )
def wwRED( *args ): wwOUT( RED, *args )
def wwBLU( *args ): wwOUT( BLU, *args )
def wwGRE( *args ): wwOUT( GRE, *args )
def wwCYA( *args ): wwOUT( CYA, *args )
def wwMAG( *args ): wwOUT( MAG, *args )
def wwYEL( *args ): wwOUT( YEL, *args )
def wwWHI( *args ): wwOUT( WHI, *args )
def wwBLA( *args ): wwOUT( BLA, *args )

def ewDEF( *args ): ewOUT( DEF, *args )
def ewRED( *args ): ewOUT( RED, *args )
def ewBLU( *args ): ewOUT( BLU, *args )
def ewGRE( *args ): ewOUT( GRE, *args )
def ewCYA( *args ): ewOUT( CYA, *args )
def ewMAG( *args ): ewOUT( MAG, *args )
def ewYEL( *args ): ewOUT( YEL, *args )
def ewWHI( *args ): ewOUT( WHI, *args )
def ewBLA( *args ): ewOUT( BLA, *args )

#======================================================================

def DBG( *args ): ewBLU( 'zciconf:', *args )
def MSG( *args ): ewCYA( 'zciconf:', *args )
def WAR( *args ): ewMAG( 'zciconf:', *args )
def ERR( *args ): ewRED( 'zciconf:', *args )

#======================================================================

class Error( Exception ):

  def __init__( self, *args ):
    ERR( *args )

  def __str__( self ):
    return 'Error'

#======================================================================
