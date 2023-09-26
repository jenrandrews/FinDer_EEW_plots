#!/bin/bash

### Kaikoura 7.8
#evid='2016p858000'
#fd_evid='nzrcet2016wiai'

### Darfield 7.1
evid='3366146'
fd_evid='nzrcet2010rgxc'

### Dusky Sound 7.6
#evid='3124785'
#fd_evid='nzrcet2009nszr'

### Eketahuna 6.2
#evid='2014p051675'
#fd_evid='nzrcet2014biyg'

### Cook Strait 6.6
#evid='2013p543824'
#fd_evid='nzrcet2013odqh'

### Lake Grassmere 6.6
#evid='2013p613797'
#fd_evid='nzrcet2013pyye'

### Christchurch 6.2
#evid='3468575'
#fd_evid='nzrcet2011dqzw'

### East Cape 7.2
#evid='2021p169083'
#fd_evid='nzrcet2021ekhv'

### FinDer source
#fd_auth='scfdrwc'
fd_auth='scfinder'

alert_method='moratalla_alert_distances.tbl'
mmi_tw=5.0 # MMI threshold for warning times and shaking of interest (not alert threshold!)

# ms2mmi will: 
# # download event, inventory and miniseed based on a GeoNet eventID
# # compute the exceedence times for mmis in range 2.5 -> 8.5 stepping every 0.5 based on miniseed PGA & PGV (median MMI)
#python ms2mmi.py $evid 

# alert_times.py will:
# # download event
# # read alert_distances.tbl ---> mag + mmi -> dist tbl created for GMPE + GMICE (see openquake scripts)
#python alert_times.py $evid $fd_evid $fd_auth $alert_method

python plots.py $evid $mmi_tw
