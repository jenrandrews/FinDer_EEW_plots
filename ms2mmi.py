import os, sys
import obspy as ob
import math
from numpy import nonzero, log10, absolute, where, arange
import geographiclib.geodesic as geo

import eew_utils as utils
import moratalla as gmice

def calcdistaz(lat1, lon1, lat2, lon2):
    '''
    Calculate distance and azimuth between two geographic points in km
    '''
    a2b = geo.Geodesic.WGS84.Inverse(lat1, lon1, lat2, lon2)
    return a2b['s12']/1000.0, a2b['azi1']


def doTimeCheck(tr, origin_time, dist):
    '''
    Check there is data in the trace in the waveform window
    '''
    # Check for relevant data window
    checktime = origin_time + (dist / 6.) - 10. # if no data after this time ignore
    if tr.stats.endtime < checktime:
        return False
    checktime = origin_time + (dist / 3.) + 30. # if no data before this time ignore
    if tr.stats.starttime > checktime:
        return False
    return True


def ms2mmi(ev, mslist, metadata):
    '''
    Compute MMI exceedence times after origin time that MMI is exceeded at a station
    Miniseed is read in and converted to acceleration and velocity using the remove_response function
    Data are demeaned and converted to cm/s/s or cm/s (from m/s/s or m/s)
    Exceedence is computed on a per-channel basis (not combined horizontals), and then the minimum time is taken from all channels for a sensor
    '''
    origin_time = ev.preferred_origin().time
    elat = ev.preferred_origin().latitude
    elon = ev.preferred_origin().longitude
    mmilevels = arange(2.5, 9, 0.5)
    exceedance_times = {}
    for ms in sorted(mslist):
        st = ob.read(ms)
        for tr in st:
            if tr.stats.location not in ['10', '20']: # This is a hack for New Zealand
                continue
            stub = tr.get_id()
            if stub not in exceedance_times:
                try:
                    sdict = metadata.get_channel_metadata(tr.get_id())
                except:
                    print(f'Failed to find metadata for {tr.get_id()}')
                    continue
                dist, az = calcdistaz(sdict['latitude'], sdict['longitude'], elat, elon)
                if not doTimeCheck(tr, origin_time, dist):
                    continue
                exceedance_times[stub] = {}
                exceedance_times[stub]['location'] = {'lat': sdict['latitude'], 'lon': sdict['longitude'], 'epidist': dist}
            inv = metadata.select(network=tr.stats.network, 
                                  station=tr.stats.station,
                                  location=tr.stats.location, 
                                  channel=tr.stats.channel)
            dist, az = calcdistaz(exceedance_times[stub]['location']['lat'], 
                                  exceedance_times[stub]['location']['lon'], 
                                  elat, 
                                  elon)
            if not doTimeCheck(tr, origin_time, dist):
                continue
            # baseline removal
            tr.detrend('demean')
            # gain correction
            tr.remove_sensitivity(inventory=inv)
            tr.data *= 100. # convert m/s/s to cm/s/s
            tr.filter('highpass', freq=0.075)
            # ground motion types
            acc = tr.copy()
            vel = tr.copy()
            if tr.stats.channel[1] == 'H': # assuming HH? = broadband and HN? = strong motion
                acc.differentiate()
            else:
                vel.integrate()
                vel.filter('highpass', freq=0.075)
            inpga = log10(where(absolute(acc.data) > 0, absolute(acc.data), 0.0001))
            inpgv = log10(where(absolute(vel.data) > 0, absolute(vel.data), 0.0001))
            mmi = gmice.gm2mmiArray(inpga, inpgv)
            if False:
                outname = f'{tr.get_id()}.png'
                i = 1
                while os.path.isfile(outname):
                    outname = f'{tr.get_id()}_{i}.png'
                    i += 1
                import matplotlib.pyplot as plt
                fig, ax = plt.subplots(5,1)
                ax[0].plot(acc.data)
                ax[0].set_ylabel('Acc')
                ax[1].plot(vel.data)
                ax[1].set_ylabel('Vel')
                ax[2].plot(mmi)
                ax[2].set_ylabel('MMI')
                ax[3].plot(inpga)
                ax[3].set_ylabel('log10(Acc)')
                ax[4].plot(inpgv)
                ax[4].set_ylabel('log10(Vel)')
                plt.savefig(outname)
            for m in mmilevels:
                ind = nonzero(mmi > m)
                if len(ind[0]) > 0: 
                    etime = tr.stats.starttime + (tr.stats.delta * ind[0][0]) - origin_time
                    #if etime < 0:
                    #    print(tr.stats, etime)
                else:
                    etime = None
                if m in exceedance_times[stub]:
                    if etime is not None:
                        if exceedance_times[stub][m] is None or etime < exceedance_times[stub][m]:
                            exceedance_times[stub][m] = etime
                else:
                    exceedance_times[stub][m] = etime
            if 'max' in exceedance_times[stub]:
                if max(mmi) > exceedance_times[stub]['max']:
                    exceedance_times[stub]['max'] = max(mmi)
            else:
                exceedance_times[stub]['max'] = max(mmi)

    exc_times = {}
    stubs = set(['.'.join(x.split('.')[:2]) for x in exceedance_times])
    for stub in sorted(stubs):
        exc_times[stub] = {}
        stnlist = [x for x in exceedance_times if '.'.join(x.split('.')[:2]) == stub and 'location' in exceedance_times[x] and len(exceedance_times[x]) > 0]
        for m in mmilevels:
            mint = None
            location = None
            for stn in stnlist:
                location = exceedance_times[stn]['location']
                if exceedance_times[stn][m] is not None:
                    if mint is None or exceedance_times[stn][m] < mint:
                        mint = exceedance_times[stn][m]
            exc_times[stub][m] = mint
            exc_times[stub]['location'] = location
        exc_times[stub]['max'] = max([exceedance_times[x]['max'] for x in stnlist])

    evid = ev.resource_id.id.split(os.path.sep)[-1]
    with open(os.path.join(evid, 'exceedance_times.tbl'), 'w') as fout:
        for stn in exc_times:
            fout.write(f'{stn} {exc_times[stn]}\n')
    return

if __name__ == '__main__':
    ###
    ### Input parameters ###
    ###
    evid = sys.argv[1] # GeoNet event ID
    ###
    ### Input parameters ###
    ###

    msdir = os.path.join(evid, f'{evid}_ms')
    msfile = os.path.join(evid, f'{evid}.ms')
    invfile = f'{evid}_inventory.xml'
    evfile = f'{evid}.xml'

    evfile = os.path.join(evid, evfile)
    if not os.path.isfile(evfile):
        client = utils.getClient()
        ev = utils.getEvent(client, evid)
        if ev is None:
            print(f'Error retrieving event with id {evid}')
            exit()
        ev.write(evfile, format='QUAKEML')
    ev = ob.read_events(evfile, format='QUAKEML')[0]

    invfile = os.path.join(evid, invfile)
    if not os.path.isfile(invfile):
        print(f'inventory file {invfile} does not exist!')
        exit()
        invfile = utils.downloadInv(client, ev)
        if invfile is None:
            print(f'Error retrieving inventory file {invfile}')
            exit()
    metadata = ob.read_inventory(invfile)

    if not os.path.isdir(msdir) and not os.path.isfile(msfile):
        print(f'miniseed directory {msdir} and file {msfile} does not exist!')
        wffiles = utils.downloadWF(client, metadata, ev)
        if wffiles is None:
            print(f'Error retrieving miniseed files')
            exit()

    if os.path.isdir(msdir):
        mslist = [os.path.join(msdir, ms) for ms in os.listdir(msdir)]
    else:
        mslist = [msfile]

    ms2mmi(ev, mslist, metadata)

