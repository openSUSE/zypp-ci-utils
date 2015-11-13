#======================================================================
import fnmatch
import cout
try:
  import __config__
except cout.Error:
  exit( 99 )
#======================================================================

#also consider unmaintained labels?
kAllLabels = False

def whichLabels():
  return 'all labels' if kAllLabels else 'maintained labels'

def label( name ):
  """Return label by name."""
  for l in __config__.labels:
    if kAllLabels or l.isMaintained:
      if l.name == name:
	return l

def labels( glob = None ):
  """Return all labels or those matching glob."""
  for l in __config__.labels:
    if kAllLabels or l.isMaintained:
      if not glob or fnmatch.fnmatch( l.name, glob  ):
	yield l

#======================================================================

def develPrj( name ):
  """Devel project associated with label."""
  if type(name) is not __config__.Label:
    name = label( name )
  return __config__.develprjs[name]

#======================================================================
