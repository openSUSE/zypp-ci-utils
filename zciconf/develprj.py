#======================================================================
import cout
#======================================================================

class Request( object ):
  """How to feed from one project into another"""
  def __init__( self, osc, rq, srcPrj, trgPrj ):
    self.osc = osc
    self.rq = rq
    self.srcPrj = osc.prj( srcPrj )
    self.trgPrj = osc.prj( trgPrj )

  def lastSubmission( self ):
    pass

  def __str__( self ):
    return "%-5s %-25s -(%s)-> %-25s" %( self.osc, self.srcPrj, self.rq, self.trgPrj)


#======================================================================

class DevelPrj( Request ):
  """Devel project and the official project it feeds."""

  def __init__( self, osc, rq, srcPrj, trgPrj, corePkgs ):
    super( DevelPrj, self ).__init__( osc, rq, srcPrj, trgPrj )
    self.corePkgs = corePkgs
    if not self.corePkgs:
      raise cout.Error( 'No core packages defined:', self )

#======================================================================
