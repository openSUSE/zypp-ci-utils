#======================================================================
import cout
import osc
#======================================================================

class Label( object ):
  """Task label

  Labels shall be ordered in the sequence they are first created
  in __config__.
  """

  _shared_state = {}

  @classmethod
  def define( cls, name ):
    maintained = True
    if name[0] == "#":
      name = name[1:]
      maintained = False
    sidx = len(cls._shared_state)
    if name in cls._shared_state:
      raise cout.Error( 'Multiple definitions for Label:', name )
    cls._shared_state[name] = { '_sidx':sidx, '_name':name, '_maintained':maintained }
    return cls( name )

  def __init__( self, name ):
    if not name in self._shared_state:
      raise cout.Error( 'Undefined Label:', name )
    self.__dict__ = self._shared_state[name]

  @property
  def name( self ):
    return self._name

  @property
  def maintained( self ):
    return self._maintained

  def __eq__( self, other ):
    try: return self.__dict__ is other.__dict__
    except: return False

  def __ne__( self, other ):
    return not self.__eq__( other )

  def __cmp__( self, other ):
    return cmp( self._sidx, other._sidx )

  def __hash__( self ):
    return hash( self._name )

  def __str__( self ):
    return self._name

#======================================================================

class LabelConfig( object ):
  """Configuration associated with a task label"""
  def __init__( self ):
    pass

  @property
  def gitBranch( self ):
    return None

  @property
  def develPrj( self ):
    return self._develPrj

  @property
  def distPrj( self ):
    return self._distPrj

  @property
  def submittReq( self ):
    return None


#======================================================================

class DistPrj( osc.Prj ):
  """Distribution project associated with a task label"""
  def __init__( self, osc, name ):
    super( self, osc, name )
    self.submittFrom = None

#======================================================================

class DevelPrj( osc.Prj ):
  """Devel project feeding one or more dist projects"""
  def __init__( self, osc, name ):
    super( self, osc, name )
    self.submittsTo = None

#======================================================================

class Feed( object ):
  """"""
  type = "->"
  def __init__( self, src, trg ):
    pass

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
