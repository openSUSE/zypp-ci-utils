#======================================================================

class Label( object ):
  """Task label"""
  _cmp = 0

  def __init__( self, name ):
    Label._cmp += 1
    self._cmp = Label._cmp
    if name[0] == "#":
      self.name = name[1:]
      self.isMaintained = False
    else:
      self.name = name
      self.isMaintained = True

  def __cmp__( self, other ):
    return cmp( self._cmp, other._cmp )

  def __str__( self ):
    return self.name

  def __repr__( self ):
    return self.name

#======================================================================
