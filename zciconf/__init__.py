#======================================================================
import fnmatch
from sets import Set
import cout
try:
  import __config__
except cout.Error:
  exit( 99 )
#======================================================================

#also consider unmaintained labels?
kAllLabels = False

def whichL():
  return 'known' if kAllLabels else 'maintained'

def whichLabel():
  return '%s label' % whichL()

def whichLabels():
  return '%s labels' % whichL()

#======================================================================

def label( name ):
  """Return label by name."""
  for l in __config__.labels:
    if kAllLabels or l.maintained:
      if l.name == name:
	return l

def labels( glob = None ):
  """Return all labels or those matching glob."""
  for l in __config__.labels:
    if kAllLabels or l.maintained:
      if not glob or fnmatch.fnmatch( l.name, glob  ):
	yield l

#======================================================================

def args2labels( args ):
  """list of globs -> list of Labels (args.LABEL from argparse)"""
  ret = Set()
  globs = args.LABEL if type(args.LABEL) is list else [ args.LABEL ]
  for glob in globs:
    gotcha = False
    for l in labels( glob ):
      ret.add( l )
      if not gotcha: gotcha = True
    if not gotcha:
      cout.elRED( 'no ', whichLabel() ,' matching \'' , glob, '\'' )
      args.EXIT = 2
  return sorted( ret )

def args2label( args ):
  """one glob -> one Label (args.LABEL from argparse)"""
  ret = None
  lset = args2labels( args )
  if lset:
    if len(lset) == 1:
      ret = lset.pop()
    else:
      cout.elRED( 'multiple ', whichLabels() , ' matching \'' , args.LABEL, '\': ', lset )
      args.EXIT = 2
  return ret

#======================================================================

def develPrj( name ):
  """Devel project associated with label."""
  if type(name) is not __config__.Label:
    name = label( name )
  return __config__.develprjs[name]

#======================================================================
