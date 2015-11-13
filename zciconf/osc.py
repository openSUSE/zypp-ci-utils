#======================================================================
import cout
import cmd
import re
from datetime import datetime
#======================================================================

def _xkvline2dict( line ):
  ret = {}
  for word in line.split():
    m = re.match( '([^=]*)="([^"]*)"', word )
    if ( m ):
      ret[m.group( 1 )] = m.group( 2 )
    elif word[0] == "<" and word[1] != "/":
      ret[0] = word[1:]
  return ret

#======================================================================

class Osc( object ):

  def ls( self, rx = None ):
    for line in self._cmd( 'ls' ):
      if rx and not re.match( rx, line ): continue
      yield Prj( self, line )

  def prj( self, name ):
    return Prj( self, name )

  @classmethod
  def _cmd( cls, *args ):
    for line in cmd.run( cls._cmdstr, *args ):
      yield line

  @classmethod
  def __str__( cls ):
    return cls._cmdstr

#======================================================================

class Obs( Osc ):
  _str = 'obs:/'
  _cmdstr = 'osc'

#======================================================================

class Ibs( Osc ):
  _str = 'ibs:/'
  _cmdstr = 'isc'

#======================================================================

class Prj( object ):

  def __init__( self, osc, name ):
    self.osc = osc
    self.name = name
    self._content = None

  @property
  def content( self ):
    if self._content is None:
      self._content = []
      for line in self.osc._cmd( 'ls', self.name ):
	self._content.append( line )
    return self._content

  def ls( self, rx = None ):
    for line in self.content:
      if rx and not re.match( rx, line ): continue
      yield Pkg( self, line )

  def pkg( self, name ):
    return Pkg( self, name )

  def __nonzero__( self ):
    return bool(self.content)

  def __str__( self ):
    return self.name

#======================================================================

class Pkg( object ):

  def __init__( self, prj, name  ):
    self.prj = prj
    self.name = name
    self._rawdata = None

  #<directory name="libzypp" rev="bc36d21b7c2f0d1f99d94ab4ee6cc345" vrev="3" srcmd5="bc36d21b7c2f0d1f99d94ab4ee6cc345">
  #  <linkinfo project="zypp:SLE-12-Branch" package="libzypp" srcmd5="7eba10346a7d1c8b89512ba2260cfaa4" lsrcmd5="38ca0e7e950ea2414b9840a45efd41c9" />
  #  <entry name="libzypp-14.42.3.tar.bz2" md5="084b400f996d3da6deb62ba54dd58953" size="5058653" mtime="1445614614" />
  #  <entry name="libzypp-rpmlintrc" md5="7da62f6548b1778d6b52fa9fca718b5c" size="47" mtime="1193863969" />
  #  <entry name="libzypp.changes" md5="cab6eac5b81e717a67fb7f6b3e16bfed" size="358419" mtime="1445614614" />
  #  <entry name="libzypp.spec" md5="8b59d1c9776e6de5c33a6d7e0f74539d" size="9420" mtime="1445614614" />
  #</directory>
  @property
  def rawdata( self ):
    if self._rawdata is None:
      self._rawdata = { 'entry' : [], 'linkinfo' : None }
      for line in self.osc._cmd( 'api', '/source/%s/%s/?rev=latest&expand=1' % ( self.prj.name, self.name ) ):
	kv = _xkvline2dict( line )
	if 0 in kv:
	  if kv[0] == 'entry':
	    f = File( self, kv )
	    self._rawdata[kv[0]].append( f )
	  elif kv[0] == 'linkinfo':
	    self._rawdata[kv[0]] = Link( self.osc, kv )
	  else:
	    self._rawdata[kv[0]] = kv
    return self._rawdata

  def ls( self, rx = None ):
    for f in self.content:
      if rx and not re.match( rx, f.name ): continue
      yield f

  @property
  def osc( self ):
    return self.prj.osc

  @property
  def content( self ):
    return self.rawdata['entry']

  @property
  def link( self ):
    return self.rawdata['linkinfo']

  @property
  def version( self ):
    if not 'version' in self.rawdata:
      m = re.search( "-([^-]*)\\.tar", self.tarball.name )
      self.rawdata['version'] = m.group( 1 ) if m else '?'
    return self.rawdata['version']

  @property
  def tarball( self ):
    if not 'tarball' in self.rawdata:
      for f in self.content:
	m = re.search( "\\.tar(\\..*)?$", f.name )
	if m:
	  self.rawdata['tarball'] = f
	  break
    return self.rawdata['tarball']

  @property
  def changes( self ):
    if not 'changes' in self.rawdata:
      for f in self.content:
	m = re.search( "\\.changes$", f.name )
	if m:
	  self.rawdata['changes'] = f
	  break
    return self.rawdata['changes']

  @property
  def specfile( self ):
    if not 'specfile' in self.rawdata:
      for f in self.content:
	m = re.search( "\\.spec$", f.name )
	if m:
	  self.rawdata['specfile'] = f
	  break
    return self.rawdata['specfile']

  @property
  def vstr( self ):
    ret = '%s %s %s' % ( self.prj.name, self.name, self.version )
    if self.link: ret += ' %s' % str(self.link)
    return ret

  def __nonzero__( self ):
    return bool(self.content)

  def __str__( self ):
    return self.name

#======================================================================

class File( object ):

  #  <entry name="libzypp-14.42.3.tar.bz2" md5="084b400f996d3da6deb62ba54dd58953" size="5058653" mtime="1445614614" />
  def __init__( self, pkg, rawdata ):
    self.pkg = pkg
    self.rawdata = rawdata

  @property
  def osc( self ):
    return self.pkg.osc

  @property
  def prj( self ):
    return self.pkg.prj

  @property
  def name( self ):
    return self.rawdata['name']

  @property
  def md5( self ):
    return self.rawdata['md5']

  @property
  def size( self ):
    return self.rawdata['size']

  @property
  def mtime( self ):
    return self.rawdata['mtime']

  @property
  def vstr( self ):
    return '%s %9s %s %s' % ( self.md5, self.size, datetime.fromtimestamp(float(self.mtime)).ctime()[4:], self.name )

  def cat( self ):
    return self.osc._cmd( 'cat', self.prj.name, self.pkg.name, self.name )

  def __eq__( self, other ):
    if type(other) is type(self):
      return self.rawdata == other.rawdata
    return False

  def __ne__( self, other ):
    return not self.__eq__( other )

  def __nonzero__( self ):
    return bool(self.name)

  def __str__( self ):
    return self.name

#======================================================================

class Link( object ):

  #  <linkinfo project="zypp:SLE-12-Branch" package="libzypp" srcmd5="7eba10346a7d1c8b89512ba2260cfaa4" lsrcmd5="38ca0e7e950ea2414b9840a45efd41c9" />
  def __init__( self, osc, rawdata ):
    self.osc = osc
    self.rawdata = rawdata

  @property
  def prj( self ):
    return self.osc.prj( self.rawdata['project'] )

  @property
  def pkg( self ):
    return self.prj.pkg( self.rawdata['package'] )

  def __str__( self ):
    return '-> %s %s' % ( self.rawdata['project'], self.rawdata['package'] )

#======================================================================
