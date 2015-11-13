#======================================================================
import osc
from label import Label
from develprj import DevelPrj
#======================================================================

# build services
obs = osc.Obs()
ibs = osc.Ibs()

# stack types
solv = [ 'libsolv', 'libzypp', 'zypper' ]
sat  = [ 'libsatsolver', 'libzypp', 'zypper' ]
zmd  = [ 'libzypp', 'zypper', 'zypp-zmd-backend' ]

#======================================================================

# the Labels
labels = []

# the DevelPrjs
develprjs = {}

#======================================================================
def _cfg( name, osc, rq, srcPrj, trgPrj, corePkgs ):
  l = Label(name)
  labels.append( l )
  develprjs[l] = DevelPrj( osc, rq, srcPrj, trgPrj, corePkgs )
#======================================================================

_cfg(	'head',		obs,	'sr',	'zypp:Head',		'openSUSE:Factory',		solv	),

_cfg(	'c42.1',	obs,	'mr',	'zypp:Code42_1-Branch',	'openSUSE:Leap:42.1:Update',	solv	),
_cfg(	'c13.2',	obs,	'mr',	'zypp:Code13_2-Branch',	'openSUSE:13.2:Update',		solv	),
_cfg(	'c13.1',	obs,	'mr',	'zypp:Code13_1-Branch',	'openSUSE:13.1:Update',		solv	),
_cfg(	'#c12.3',	obs,	'mr',	'zypp:Code12_3-Branch',	'openSUSE:12.3:Update',		solv	),
_cfg(	'#c12.2',	obs,	'mr',	'zypp:Code12_2-Branch',	'openSUSE:12.2:Update',		solv	),
_cfg(	'#c12.1',	obs,	'mr',	'zypp:Code12_1-Branch',	'openSUSE:12.1:Update',		solv	),
#_cfg(	'#c11.4',	obs,	'mr',	'zypp:Code11_4-Branch',	'openSUSE:11.4:Update',		sat	),
#_cfg(	'#c11.3',	obs,	'sr',	'zypp:Code11_3-Branch',	'openSUSE:11.3:Update',		sat	),
#_cfg(	'#c11.2',	obs,	'sr',	'zypp:Code11_2-Branch',	'openSUSE:11.2:Update',		sat	),
#_cfg(	'#c11',		obs,	'sr',	'zypp:Code11-Branch',	'openSUSE:11.1:Update',		sat	),

_cfg(	's12sp1',	ibs,	'sr',	'Devel:zypp:SLE12SP1',	'SUSE:SLE-12-SP1:GA',		solv	),
_cfg(	's12',		ibs,	'mr',	'Devel:zypp:SLE12',	'SUSE:SLE-12:Update',		solv	),

_cfg(	's11sp4',	ibs,	'sr',	'Devel:zypp:SLE11SP4',	'SUSE:SLE-11-SP4:Update',	sat	),
_cfg(	's11sp3',	ibs,	'sr',	'Devel:zypp:SLE11SP3',	'SUSE:SLE-11-SP3:Update',	sat	),
_cfg(	'#s11sp2',	ibs,	'sr',	'Devel:zypp:SLE11SP2',	'SUSE:SLE-11-SP2:Update',	sat	),
_cfg(	'#s11sp1',	ibs,	'sr',	'Devel:zypp:SLE11SP1',	'SUSE:SLE-11-SP1:Update',	sat	),
_cfg(	'#s11',		ibs,	'sr',	'Devel:zypp:SLE11',	'SUSE:SLE-11:Update',		sat	),

_cfg(	's10sp4',	ibs,	'sr',	'Devel:zypp:SLE10-SP4',	'SUSE:SLE-10-SP4:Update:Test',	zmd	),

#_cfg(	'#smgr',	ibs,	'sr',	'Devel:zypp:SLE11SP1',	'SUSE:SLE-11-SP1:Update:Test',			sat	),
#_cfg(	'#smgrC10.1.7',	ibs,	'sr',	'Devel:zypp:SLE11SP1',	'SUSE:SLE-10-SP3:Manager:1.7:Update:Test',	sat	),
#_cfg(	'#smgrC10.1.2',	ibs,	'sr',	'Devel:zypp:SLE11SP1',	'SUSE:SLE-10-SP3:Manager:1.2:Update:Test',	sat	),

#======================================================================
