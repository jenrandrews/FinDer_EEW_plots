#!/bin/bash
#
### FinDer source
#fd_auth='scfdrwc'
fd_auth='scfinder'

alert_method='moratalla_alert_distances.tbl'
mmi_tw=5.0 # MMI threshold for warning times and shaking of interest (not alert threshold!)
#mag_w=5.5 # Magnitude threshold for issuing an alert
#latency=0 # 10.s Allow 3 seconds for data transmission, extra compute, 7 seconds for alert distribution (ref. cell phone apps)

evid=''
fd_evid=''

### 2007_GeorgeSound_6.7
#evid+=' 2808298'
#fd_evid+=' nzrcet2007ufic'

### 2007_EastCoast_6.7
#evid+=' 2839343'
#fd_evid+=' nzrcet2007yvog'

### 2009_DuskySound_7.8
#evid+=' 3124785'
#fd_evid+=' nzrcet2009nszr'

### 2009_Fiordland_6.1
#evid+=' 3134797'
#fd_evid+=' nzrcet2009pfho'

### 2009_Puysegur_6.1
##evid+=' 3308618'
##fd_evid+=' nzrcet2009ntah'

### 2010_Darfield_7.2
#evid+=' 3366146'
#fd_evid+=' nzrcet2010rgxc'

### 2011_Christchurch_6.2
evid+=' 3468575'
fd_evid+=' nzrcet2011dqzw'

### 2011_Christchurch_6.0
#evid+=' 3528839'
#fd_evid+=' nzrcet2011llzq'

### 2012_Whanganui_6.2
#evid+=' 2012p498491'
#fd_evid+=' nzrcet2012myzo'

### 2013_CookStrait_6.5
#evid+=' 2013p543824'
#fd_evid+=' nzrcet2013odqi'

### 2013_LakeGrassmere_6.6
#evid+=' 2013p613797'
#fd_evid+=' nzrcet2013pyye'

### 2013_Puysegur_6.1
#evid+=' 2013p944608'
#fd_evid+=' nzrcet2013yooo'

### 2014_Eketahuna_6.2
#evid+=' 2014p051675'
#fd_evid+=' nzrcet2014biyg'

### 2014_Puysegur_6.2
#evid+=' 2014p770859'
#fd_evid+=' nzrcet2014ubcs'

### 2015_ArthursPass_6.0
#evid+=' 2015p012816'
#fd_evid+=' nzrcet2015airg'

### 2015_StArnaud_6.2
#evid+=' 2015p305812'
#fd_evid+=' nzrcet2015hysz'

### 2015_Wanaka_5.8
#evid+=' 2015p332712'
#fd_evid+=' nzrcet2015iqxu'

### 2016_EastCape_7.1
#evid+=' 2016p661332'
#fd_evid+=' nzrcet2016rfbr'

### 2016_EastCape_6.2
#evid+=' 2016p661400'
#fd_evid+=' nzrcet2016rfcw'

### 2016_EastCape_6.0
#evid+=' 2016p661723'
#fd_evid+=' nzrcet2016rfio'

### 2016_Kaikoura_7.8
#evid+=' 2016p858000'
#fd_evid+=' nzrcet2016wiai'

### 2016_Seddon_6.0
#evid+=' 2016p858007'
#fd_evid+=' nzrcet2016wiaj'

### 2016_Kaikoura_6.0
#evid+=' 2016p858021'
#fd_evid+=' nzrcet2016wiap'

### 2016_Kaikoura_6.2
#evid+=' 2016p858055'
#fd_evid+=' nzrcet2016wibg'

### 2016_Kaikoura_6.1
#evid+=' 2016p858094'
#fd_evid+=' nzrcet2016wiby'

### 2016_HanmerSprings_6.7
#evid+=' 2016p859524'
#fd_evid+=' nzrcet2016wjbc'

### 2018_Taumurunui_6.2
#evid+=' 2018p816466'
#fd_evid+=' nzrcet2018vfyi'

### 2020_Whanganui_5.8
#evid+=' 2020p391429'
#fd_evid+=' nzrcet2020kepv'

### 2021_EastCape_7.3
#evid+=' 2021p169083'
#fd_evid+=' nzrcet2021ekhv'

### 2021_EastCape_6.2
#evid+=' 2021p173004'
#fd_evid+=' nzrcet2021emyt'

### 2021_EastCape_6.0
#evid+=' 2021p254914'
#fd_evid+=' nzrcet2021gqik'

### 2022_Taupo_5.7
#evid+=' 2022p901216'
#fd_evid+=' nzrcet2022xlfx'

### 2023_Whanganui_6.0
#evid+=' 2023p122368'
#fd_evid+=' nzrcet2023desu'

### 2023_Porangahau_5.9
#evid+=' 2023p310616'
#fd_evid+=' nzrcet2023ibzl'

### 2023_Geraldine_6.0
#evid+=' 2023p707798'
#fd_evid+=' nzrcet2023skmj'

read -ra evids <<< "$evid"
read -ra fd_evids <<< "$fd_evid"

for ((idx = 0; idx < ${#evids[@]}; idx++)); do
  for mag_w in 4.5 5.5; do
#    for latency in 0 5 10; do
    for latency in 4; do
      evid=${evids[idx]}
      fd_evid=${fd_evids[idx]}
      echo $idx $evid $fd_evid

      # ms2mmi will: 
      # # download event, inventory and miniseed based on a GeoNet eventID
      # # compute the exceedence times for mmis in range 2.5 -> 8.5 stepping every 0.5 based on miniseed PGA & PGV (median MMI)
      if [ ! -f ${evid}/exceedance_times.tbl ]; then
        python ms2mmi.py $evid 
      fi

      # fdsol_plots.py will:
      # # create basic plots of the FinDer alerts
      if [ ! -f ${evid}/${evid}_fdsol_mag.png ]; then
        python fdsol_plots.py $evid $fd_evid $fd_auth
      fi

      # alert_times.py will:
      # # download event based on a GeoNet eventID
      # # compute alert_distances.tbl ---> mag + mmi -> dist tbl created for GMPE + GMICE (see openquake scripts)
      if [ ! -f ${evid}/alert_times_${mag_w}_${latency}.tbl ]; then
        echo 'Calculating alert table'
        python alert_times.py $evid $fd_evid $fd_auth $alert_method $mag_w $latency
      fi

      # Plotting
      if true; then
        python plots.py $evid $mmi_tw $mag_w $latency
        plotdir="plots_latency-${latency}_mag-${mag_w}_mmitw-${mmi_tw}"
        if [ ! -d ${evid}/${plotdir} ]; then
          mkdir ${evid}/${plotdir}
        fi
        mv ${evid}/${evid}_mmi*.png ${evid}/*_mmi*.dat ${evid}/${plotdir}
      fi
    done
  done
done
