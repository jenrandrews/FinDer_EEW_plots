import os
from obspy.clients.fdsn import Client

def getClient():
    return Client("GEONET")

def getEvent(client, evid, debug=False):
    '''
    Get Event from GeoNet 
    '''
    cat = client.get_events(eventid=evid)
    if debug:
        print(cat)  
        cat.plot() 
    if len(cat) == 0:
        return None
    return cat[0]

def downloadInv(client, ev):
    '''
    Using an event id and region FDSN client, download metadata (inventory)
    and waveforms (one miniseed per channel)
    Args:
        client: obspy FDSN Client
        ev: obspy Event object
    Return:
        inventory: response-level obspy inventory with all stations for data download
    '''
    evid = ev.resource_id.id.split(os.path.sep)[-1]
    orig = ev.preferred_origin()
    origt = orig.time
    # Get station inventory
    try:
        inventory = client.get_stations(startbefore=origt, endafter=origt, level='response', \
                latitude=orig.latitude, longitude=orig.longitude, maxradius=10., channel='HH?,HN?') 
    except:
        print('Failed to download inventory')
        exit()
    foutxml = os.path.join(evid, f'{evid}_inventory.xml')
    inventory.write(foutxml, format='STATIONXML')
    return foutxml

def downloadWF(client, inventory, ev):
    '''
    Using an event id and region FDSN client, download metadata (inventory)
    and waveforms (one miniseed per channel)
    Args:
        client: obspy FDSN Client
        ev: obspy Event object
    Return:
        stlist: list of miniseed file names
    '''
    evid = ev.resource_id.id.split(os.path.sep)[-1]
    orig = ev.preferred_origin()
    mag = ev.preferred_magnitude()
    origt = orig.time
    # Get event waveforms
    t1 = origt - 120
    t2 = origt + 300
    stlist = []
    msdir = os.path.join(evid, '_'.join([evid, 'ms']))
    if not os.path.isdir(msdir):
        os.mkdir(msdir)
    for inst in set([x[:-1] for x in inventory.get_contents()['channels']]):
        fname = '%s_%s.ms' % (evid, inst)
        stfname = os.path.join(msdir, fname)
        if os.path.isfile(stfname):
            stlist.append(stfname)
            continue
        s = inst.split('.')
        if s[3][0] not in ['H']: # high-rate
            continue
        if s[3][1] not in ['H', 'N']: # BB or SM
            continue
        try:
            st = client.get_waveforms(s[0], s[1], s[2], '%s?'%s[3], t1, t2)
        except:
            print('No data returned for %s'%inst)
            continue
        stlist.append(stfname)
        st.write(stfname, format='MSEED')
    if len(stlist) == 0:
        return None
    return stlist
