#======================================================================
import cout
import select
import subprocess
#======================================================================

def _readByLine( stream ):
  while True:
    line = stream.readline()
    if line: yield line
    else: break

#======================================================================

def run( *args ):
  #cout.peGRE( 'EXEC ', " ".join( args ) )
  p = subprocess.Popen( args, stdout=subprocess.PIPE, stderr=subprocess.PIPE )
  reads = [p.stdout.fileno(), p.stderr.fileno()]

  while reads:
    if p.poll() is None:
      try:
	ret = select.select( reads, [], [] )
      except select.error, v:
	if v[0] != errno.EINTR: raise
      else:
	continue
    else:
      ret = [ reads ]
      reads = None

    for fd in ret[0]:
      if fd == p.stdout.fileno():
	for line in _readByLine( p.stdout ):
	  #cout.eBLU( ' > ', line )
	  yield line[:-1]	# wo. NL
      if fd == p.stderr.fileno():
	for line in _readByLine( p.stderr ):
	  cout.eRED( '*** ', line )

#======================================================================
