import os, sys
import obspy as ob
import math
from numpy import nonzero, log10, absolute, where, arange

import eew_utils as utils
import moratalla as gmice

def ms2mmi(ev, mslist, metadata):
    '''
    Compute MMI exceedence times after origin time that MMI is exceeded at a station
    Miniseed is read in and converted to acceleration using the remove_response function
    Data are demeaned and converted to cm/s/s (from m/s/s)
    Exceedence is computed on a per-channel basis (not combined horizontals), and then the minimum time is taken from all channels for a sensor
    '''
    origin_time = ev.preferred_origin().time
    mmilevels = arange(2.5, 9, 0.5)
    exceedance_times = {}
    for ms in sorted(mslist):
        st = ob.read(ms)
        for tr in st:
            stub = tr.get_id()
            exceedance_times[stub] = {}
            try:
                sdict = metadata.get_channel_metadata(tr.get_id())
            except:
                print('Failed to find metadata for', tr.get_id())
                continue
            inv = metadata.select(network=tr.stats.network, station=tr.stats.station, \
                    location=tr.stats.location, channel=tr.stats.channel)
            exceedance_times[stub]['location'] = {'lat': sdict['latitude'], 'lon': sdict['longitude']}
            tr.remove_sensitivity(inventory=inv)
            tr.detrend('demean')
            tr.data *= 100. # convert m/s/s to cm/s/s
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
                import matplotlib.pyplot as plt
                fig, ax = plt.subplots(3,1)
                ax[0].plot(acc.data)
                ax[1].plot(vel.data)
                ax[2].plot(mmi)
                plt.savefig(f'{tr.get_id()}.png')
            for m in mmilevels:
                ind = nonzero(mmi > m)
                if len(ind[0]) > 0: 
                    etime = tr.stats.starttime + (tr.stats.delta * ind[0][0]) - origin_time
                else:
                    etime = None
                exceedance_times[stub][m] = etime
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

    msdir = os.path.join(evid, '_'.join([evid, 'ms']))
    invfile = f'{evid}_inventory.xml'

    client = utils.getClient()
    ev = utils.getEvent(client, evid)
    if ev is None:
        print(f'Error retrieving event with id {evid}')
        exit()

    invfile = os.path.join(evid, invfile)
    if not os.path.isfile(invfile):
        print(f'inventory file {invfile} does not exist!')
        invfile = utils.downloadInv(client, ev)
        if invfile is None:
            print(f'Error retrieving inventory file {invfile}')
            exit()
    metadata = ob.read_inventory(invfile)

    if not os.path.isdir(msdir):
        print(f'miniseed directory {msdir} does not exist!')
        wffiles = utils.downloadWF(client, metadata, ev)
        if wffiles is None:
            print(f'Error retrieving miniseed files')
            exit()

    mslist = [os.path.join(msdir, ms) for ms in os.listdir(msdir)]
    ms2mmi(ev, mslist, metadata)
