import sys
import os
import math
import obspy as ob
from obspy import UTCDateTime
import xml.etree.ElementTree as ET 
import geographiclib.geodesic as geo
from numpy import interp, log10, array, flip

import eew_utils as utils
import moratalla as gmice

def initialiseFDSOL(evid=''):
    fdsol = {}
    fdsol['evid'] = evid
    fdsol['mag_regr'] = -1.
    fdsol['mag_rup'] = -1.
    fdsol['mag'] = -1.
    fdsol['depth'] = -1.
    fdsol['author'] = ''
    fdsol['tstep'] = -1
    fdsol['flen'] = -1.
    fdsol['fstrike'] = -1.
    fdsol['version'] = -1
    fdsol['vtime'] = UTCDateTime(1900,1,1)
    fdsol['uncr'] = -1.
    fdsol['elat'] = -1.
    fdsol['elon'] = -1.
    fdsol['origin_time'] = UTCDateTime(1900,1,1)
    return fdsol

def scxml2fdsol(xml):
    '''
    Reads the XML produced by scxmldump (SeisComp utility to dump db contents for an event ID) and
    populates a FinDer solution dictionary (fdsol) that is passed for plotting.
    Args:
        xml: XML output from scxmldump
    Returns:
        fdsols: list of FinDer solution dictionaries. Dictionaries contain entries for: 
        version number and time, magnitudes, fault length, strike, epicentral location, 
        fault coordinates, uncertainty
    '''

    def getElem(obj, name1, name2):
        if obj is None:
            return '-9'
        if obj.find(f'solution:{name1}', ns) is None:
            return '-9'
        if obj.find(f'solution:{name1}', ns).find(f'solution:{name2}', ns) is None:
            return '-9'
        return obj.find(f'solution:{name1}', ns).find(f'solution:{name2}', ns).text.rstrip().lstrip()

    def getLatLon(lat, lon, azi, dist):
        dist *= 1000.0
        ret = geo.Geodesic.WGS84.Direct(lat, lon, azi, dist)
        return [ret['lat2'], ret['lon2']]

    # Read the xml
    try:
        root = ET.fromstring(xml)
    except:
        return False, [], {}, 0.

    # Parse following https://docs.python.org/3/library/xml.etree.elementtree.html#parsing-xml
    ns = {'solution': root.tag.split('{')[1].split('}')[0]}

    # Get the overall event info
    fdevent = {}
    event = [x for x in root.iter(f'{{{ns["solution"]}}}event')]
    if len(event) > 0:
        fdevent['evid'] = event[0].attrib['publicID'].rstrip()
        fdevent['locstr'] = getElem(event[0], 'description', 'text')
    else:
        return False, [], {}, 0.

    # Get the full origin set
    searchtag = f'{{{ns["solution"]}}}origin'
    fdsols = []
    for origin in root.iter(searchtag):
        ct = getElem(origin, 'creationInfo', 'creationTime')
        if ct == '-9':
            fdsol = []
        else:
            creationtime = UTCDateTime().strptime(ct, '%Y-%m-%dT%H:%M:%S.%fZ')
            fdsol = [f for f in fdsols if f['vtime'] == creationtime]
        if len(fdsol) == 0: 
            fdsol = initialiseFDSOL(fdevent['evid'])
            fdsol['vtime'] = creationtime
            tv = getElem(origin, 'time', 'value')
            if tv == '-9':
                fdsol['origin_time'] = UTCDateTime().now()
            else:
                fdsol['origin_time'] = UTCDateTime().strptime(tv, '%Y-%m-%dT%H:%M:%S.%fZ')
            fdsols.append(fdsol)
        else:
            fdsol = fdsol[0]
        otype = origin.find('solution:type', ns)
        if otype == None:
            fdsol['elat'] = float(getElem(origin, 'latitude', 'value'))
            fdsol['elon'] = float(getElem(origin, 'longitude', 'value'))
            fdsol['depth'] = float(getElem(origin, 'depth', 'value'))
        elif otype.text == 'centroid':
            fdsol['clat'] = float(getElem(origin, 'latitude', 'value'))
            fdsol['clon'] = float(getElem(origin, 'longitude', 'value'))
            fdsol['author'] = getElem(origin, 'creationInfo', 'author').split('@')[0]
        for mag in origin.findall('solution:magnitude', ns):
            mtype = mag.find('solution:type', ns).text.rstrip().lstrip()
            if mtype == 'Mfd':
                fdsol['mag'] = float(getElem(mag, 'magnitude', 'value'))
                for comm in mag.findall('solution:comment', ns):
                    ctype = comm.find('solution:id', ns).text
                    if ctype == 'rupture-strike':
                        fdsol['fstrike'] = float(comm.find('solution:text', ns).text.rstrip().lstrip())
                    elif ctype == 'rupture-length':
                        fdsol['flen'] = float(comm.find('solution:text', ns).text.rstrip().lstrip())
                    elif ctype == 'likelihood':
                        fdsol['uncr'] = float(comm.find('solution:text', ns).text.rstrip().lstrip())
            elif mtype == 'Mfdl':
                fdsol['mag_rup'] = float(getElem(mag, 'magnitude', 'value'))
            elif mtype == 'Mfdr':
                fdsol['mag_regr'] = float(getElem(mag, 'magnitude', 'value'))
    if len(fdsols) == 0:
        return False, [], {}, 0.
    # Add versions and compute fcoords from centroid, strike and length
    ind = 0
    for fdsol in sorted(fdsols, key=lambda x:x['vtime']):
        fdsol['version'] = ind
        ind += 1
        if 'clat' not in fdsol or 'clon' not in fdsol or 'fstrike' not in fdsol or 'flen' not in fdsol or fdsol['flen'] < 0.:
            continue
        end1 = getLatLon(fdsol['clat'], fdsol['clon'], fdsol['fstrike'], fdsol['flen']/2.)
        end2 = getLatLon(fdsol['clat'], fdsol['clon'], fdsol['fstrike']+180., fdsol['flen']/2.)
        fdsol['fcoords'] = [end1, [fdsol['clat'], fdsol['clon']], end2]
    # Time of last update
    lastt = max([f['vtime'] for f in fdsols])
    return True, fdsols, fdevent, lastt

def calcdistaz(lat1, lon1, lat2, lon2):
    '''
    Calculate distance and azimuth between two geographic points in km
    '''
    a2b = geo.Geodesic.WGS84.Inverse(lat1, lon1, lat2, lon2)
    return a2b['s12']/1000.0, a2b['azi1']

def rdAlertDists(fname):
    '''
    Alert strategy: for a contour-based (simple) alert system, want mag + MMI -> distance
    '''
    alerts = {}
    with open(fname, 'r') as fin:
        for l in fin:
            if l.startswith('#'):
                continue
            fs = l.split()
            mag = float(fs[0])
            if mag not in alerts:
                alerts[mag] = {}
            mmi = float(fs[1])
            if fs[-1] == '-1':
                dist = None
            else:
                dist = float(fs[-1])
            alerts[mag][mmi] = dist
    return alerts

def rdSites(fname):
    '''
    File with station triplets: name lat lon
    '''
    stns = {}
    metadata = ob.read_inventory(fname)
    for stn in metadata.get_contents()['stations']:
        stnname = stn.split()[0].split('.')[1]
        sinv = metadata.select(station=stnname)
        schan = sinv.get_contents()['channels'][0]
        sdict = metadata.get_channel_metadata(schan)
        stns[stn.split()[0]] = [sdict['latitude'], sdict['longitude']]
    return stns

def rdAlerts(fname, author, mag_w, latency):
    '''
    Create from xml FinDer solutions, EEW alerts in dictionary form:
    tstr: timestring for the alert UTCDateTime
    clat: rupture centroid lat
    clon: rupture centroid lon
    alat: rupture end 1 lat
    alon: rupture end 1 lon
    zlat: rupture end 2 lat
    zlon: rupture end 2 lon
    mag: magnitude
    '''
    with open(fname, 'r') as fin:
        txt = fin.read()
    ret, fdsols, fdevent, lastt = scxml2fdsol(txt)
    alerts = []
    for fd in [f for f in fdsols if f['author'] == author]:
        if fd['mag'] < mag_w:
            print(f'Ignoring alert as mag below threshold {fd}')
            continue
        alert = {'tstr': fd['vtime']+latency,
                'clat': fd['clat'],
                'clon': fd['clon'],
                'elat': fd['elat'],
                'elon': fd['elon'],
                'alat': fd['fcoords'][0][0],
                'alon': fd['fcoords'][0][1],
                'zlat': fd['fcoords'][-1][0],
                'zlon': fd['fcoords'][-1][1],
                'mag': fd['mag']}
        alerts.append(alert)
    return alerts

def computeNearestDist(slat, slon, elat1, elon1, elat2, elon2):
    '''
    Nearest distance from point to line using Herons formula semiperimeter
    elat/elon define the line endpoints
    slat/slon is the point of interest
    '''
    dist1, az1 = calcdistaz(slat, slon, elat1, elon1)
    baz1 = az1 + 180. if az1 < 0. else az1 - 180.
    dist2, az2 = calcdistaz(slat, slon, elat2, elon2)
    baz2 = az2 + 180. if az2 < 0. else az2 - 180.
    flen, az = calcdistaz(elat1, elon1, elat2, elon2) ## check which way round this needs to be!
    baz = az + 180. if az < 0. else az - 180.
    cdist = dist1 if dist1 < dist2 else dist2
    if abs(az - baz1) < 90. and abs(baz - baz2) < 90.:
        semiperim = (dist1 + dist2 + flen) / 2.
        area = math.sqrt(semiperim * (semiperim - dist1) * (semiperim - dist2) * (semiperim - flen))
        cdist = area * 2. / flen
    return cdist

def computeAlerts(ev, sites, alerts, adists):
    '''
    Compute alert times per site:
    Name {'location': [lat, lon], 'dist': closest distance to fault in km, 2.0: seconds after origin for alert at this MMI, 3.0: etc.}
    '''
    evid = ev.resource_id.id.split(os.path.sep)[-1]
    origin_time = ev.preferred_origin().time
    salerts = {}
    salerts['times'] = [a['tstr'] - origin_time for a in alerts]
    for site in sites:
        salerts[site] = {}
        salerts[site]['location'] = sites[site]
        salerts[site]['pred'] = []
        for alert in alerts:
            dist = computeNearestDist(
                    sites[site][0], sites[site][1], 
                    alert['alat'], alert['alon'], 
                    alert['zlat'], alert['zlon'])
            salerts[site]['dist'] = dist
            for mmi in adists[alert['mag']]:
                if adists[alert['mag']][mmi] is None:
                    continue
                if mmi in salerts[site]:
                    continue
                if adists[alert['mag']][mmi] > dist:
                    salerts[site][mmi] = alert['tstr'] - origin_time
            # Interpolate adists to get predMMI for this mag, dist; save max to salerts[site]['max']
            predmmi = interp(math.log10(dist), 
                    flip(log10(array([adists[alert['mag']][m] for m in adists[alert['mag']]]))),
                    flip(array([m for m in adists[alert['mag']]])))
            salerts[site]['pred'].append(predmmi)
    with open(os.path.join(evid, f'alert_times_{mag_w:.1f}_{latency:.0f}.tbl'), 'w') as fout:
        for site in sorted(salerts):
            fout.write(f'{site} {salerts[site]}\n')
    return

def printFirstAlert(ev, alerts):
    '''
    Print first alert
    '''
    origin_time = ev.preferred_origin().time
    for a in alerts:
        print(f'{a["tstr"] - origin_time}: {a}')
        #break

    return

if __name__ == '__main__':
    ###
    ### Input parameters ###
    ###
    geonet_evid = sys.argv[1] # GeoNet event ID
    fd_evid = sys.argv[2] # FinDer event ID
    author = sys.argv[3] # FinDer pipeline author
    adistfile = sys.argv[4] # Alert distance file
    mag_w = float(sys.argv[5]) # Alert magnitude threshold
    latency = float(sys.argv[6]) # Added latency for alerts (judgement)
    ###
    ### Input parameters ###
    ###

    alertfile = os.path.join(geonet_evid, f'{fd_evid}.xml')
    if not os.path.isfile(alertfile):
        print(f'Error missing FinDer event with id {fd_evid}')
        exit()

    evfile = os.path.join(geonet_evid, f'{geonet_evid}.xml')
    if not os.path.isfile(evfile):
        client = utils.getClient()
        ev = utils.getEvent(client, geonet_evid)
        if ev is None:
            print(f'Error retrieving event with id {geonet_evid}')
            exit()
        ev.write(evfile, format='QUAKEML')
    ev = ob.read_events(evfile, format='QUAKEML')[0]

    alerts = rdAlerts(alertfile, author, mag_w, latency)
    sites = rdSites(os.path.join(geonet_evid, f'{geonet_evid}_inventory.xml'))
    #printFirstAlert(ev, alerts)
    adists = rdAlertDists(adistfile)
    computeAlerts(ev, sites, alerts, adists)
