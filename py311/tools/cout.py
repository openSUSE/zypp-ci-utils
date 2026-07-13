import sys
#======================================================================
def _print( ansi, *args, **kwargs  ):
    sep = kwargs.get( 'sep', ' ' )
    end = kwargs.get( 'end', '\n' )
    print( ansi, end='' )
    print( *args, sep=sep, end='' )
    print( "\033[0m", end=end )

#======================================================================
def Rprint( *args, **kwargs ): _print( "\033[0;31m", *args, **kwargs )
def Gprint( *args, **kwargs ): _print( "\033[0;32m", *args, **kwargs )
def Bprint( *args, **kwargs ): _print( "\033[0;34m", *args, **kwargs )
def Cprint( *args, **kwargs ): _print( "\033[0;36m", *args, **kwargs )
def Mprint( *args, **kwargs ): _print( "\033[0;35m", *args, **kwargs )
def Yprint( *args, **kwargs ): _print( "\033[0;33m", *args, **kwargs )
def Pprint( *args, **kwargs ): print( *args, **kwargs )
