import sys
import os
from numpy import arange, histogram, cumsum, flip
import matplotlib as mpl
from matplotlib.pyplot import cm
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import cartopy
import cartopy.crs as ccrs
from cartopy.io.img_tiles import GoogleTiles

bTitles = False

def setBasemap(bounds = None):
    '''
    Create the basic map, including projection, extent. Add coastlines, gridlines and background
    image based on Stamen terrain map tiles.
    Args:
        bounds: xmin, xmax, ymin, ymax as list or tuple
    Returns:
        fig, axes, proj: figure, axis and projection 
    '''
    tiler = GoogleTiles(style='satellite')
    proj = tiler.crs
    fig = Figure(figsize=(5,5))
    ax = fig.add_subplot(111, projection = proj)
    if bounds == None:
        bounds = [166.0, 179.0, -47.5, -34.0]
    ax.set_extent(bounds, crs=ccrs.PlateCarree())
    #ax.add_image(tiler, 8, alpha=0.7, zorder=0.)
    # ax.coastlines(resolution='50m') # requires download
    gl = ax.gridlines(draw_labels=True, linestyle='--')
    gl.top_labels = False
    gl.right_labels = False
    return fig, ax, ccrs.PlateCarree()

def plotObsMaps(evid, obs, zoom=False):
    '''
    Plot observation maps, observed MMI
    '''
    if zoom:
        # Zoom map to event
        import eew_utils as utils
        client = utils.getClient()
        ev = utils.getEvent(client, evid)
        evlat = ev.preferred_origin().latitude
        evlon = ev.preferred_origin().longitude
        # Prevent longitude wrap around
        if evlon > 179.:
            evlon = 178.
        evbounds = [evlon-1., evlon+1., evlat-1., evlat+1.]
    if zoom:
        fig, ax, proj = setBasemap(bounds=evbounds)
    else:
        fig, ax, proj = setBasemap()
    ax.add_feature(cartopy.feature.OCEAN, zorder=2, facecolor='white', edgecolor='grey', lw=0.5)
    if bTitles:
        ax.set_title(f'Observed MMI')
    cb = ax.scatter([obs[x]['location']['lon'] for x in obs], 
            [obs[x]['location']['lat'] for x in obs], 
            c=[obs[x]['max'] for x in obs], 
            transform=proj, cmap='jet', lw=0.5, edgecolor='k', zorder=3)
    cbar = fig.colorbar(cb, ax=ax)
    cbar.set_label('observed MMI')
    if zoom:
        fig.savefig(os.path.join(evid, f'{evid}_map-obs-zoom.png'), bbox_inches='tight')
    else:
        fig.savefig(os.path.join(evid, f'{evid}_map-obs.png'), bbox_inches='tight')
    plt.close()
    return

def plotMaps(evid, mmi_tw, mag_w, latency, alert_cats, alerts, obs, zoom=False):
    '''
    Plot alert maps
    '''
    if zoom:
        # Zoom map to event
        import eew_utils as utils
        client = utils.getClient()
        ev = utils.getEvent(client, evid)
        evlat = ev.preferred_origin().latitude
        evlon = ev.preferred_origin().longitude
        if evlon > 179.:
            evlon = 178.
        evbounds = [evlon-1., evlon+1., evlat-1., evlat+1.]

    # Plot categories map
    win = cm.winter
    win.set_over('b')
    win.set_under('b')
    win.set_bad('b')
    tmin = 0.
    if evid == '2016p858000':
        tmax = 120.
    elif evid == '3366146':
        tmax = 35.
    else:
        tmax = 35.
    for mmi_a in alert_cats:
        plt.clf()
        if zoom:
            fig, ax, proj = setBasemap(bounds=evbounds)
        else:
            fig, ax, proj = setBasemap()
        ax.add_feature(cartopy.feature.OCEAN, zorder=2, facecolor='white', edgecolor='grey', lw=0.5)
        if bTitles:
            ax.set_title(f'Latency: {latency}s, Mag: {mag_w}\nMMI_tw: {mmi_tw}, MMI_alert: {mmi_a}')
        cb = ax.scatter([alerts[x]['location'][1] for x in alert_cats[mmi_a]['TPT']], 
                [alerts[x]['location'][0] for x in alert_cats[mmi_a]['TPT']], 
                c=[obs[x][mmi_tw]-alerts[x][mmi_a] for x in alert_cats[mmi_a]['TPT']], 
                transform=proj, cmap=win, lw=0.5, edgecolor='k', zorder=3, label='TP timely', s=15,
                vmin = tmin, vmax = tmax)
        ax.scatter([alerts[x]['location'][1] for x in alert_cats[mmi_a]['TPL']], 
                [alerts[x]['location'][0] for x in alert_cats[mmi_a]['TPL']], 
                transform=proj, c='yellow', lw=0.5, edgecolor='k', zorder=3, label='TP timely < MMI_tw', s=15)
        ax.scatter([alerts[x]['location'][1] for x in alert_cats[mmi_a]['TPU']], 
                [alerts[x]['location'][0] for x in alert_cats[mmi_a]['TPU']], 
                transform=proj, c='black', lw=0.5, edgecolor='k', zorder=3, label='TP untimely', s=15)
        ax.scatter([alerts[x]['location'][1] for x in alert_cats[mmi_a]['FP']], 
                [alerts[x]['location'][0] for x in alert_cats[mmi_a]['FP']], 
                transform=proj, c='orange', lw=0.5, edgecolor='k', zorder=3, label='FP', s=15)
        ax.scatter([alerts[x]['location'][1] for x in alert_cats[mmi_a]['FN']], 
                [alerts[x]['location'][0] for x in alert_cats[mmi_a]['FN']], 
                transform=proj, c='red', lw=0.5, edgecolor='k', zorder=3, label='FN', s=15)
        ax.scatter([alerts[x]['location'][1] for x in alert_cats[mmi_a]['TN']], 
                [alerts[x]['location'][0] for x in alert_cats[mmi_a]['TN']], 
                transform=proj, c='white', lw=0.5, edgecolor='k', zorder=3, label='TN', s=15)
        handles, labels = ax.get_legend_handles_labels()
        fig.legend(loc='upper left')
        cbar = fig.colorbar(cb, ax=ax)
        cbar.set_label('warning time (s)')
        if zoom:
            fig.savefig(os.path.join(evid, f'{evid}_mmi{mmi_a}_map-zoom.png'), bbox_inches='tight')
        else:
            fig.savefig(os.path.join(evid, f'{evid}_mmi{mmi_a}_map.png'), bbox_inches='tight')
    plt.close()
    return

def plotScatterMMI(evid, mmi_tw, mag_w, alert_cats, alerts, obs):
    '''
    Plot scatter plots, observed vs predicted MMI
    '''
    win = cm.winter
    win.set_over('b')
    win.set_under('b')
    win.set_bad('b')
    cols = {'TN': 'white', 'FN': 'red', 'FP': 'orange'}
    for mmi_a in alert_cats:
        plt.clf()
        fig, ax = plt.subplots(1, 1, figsize=(5,5))
        ax.axvline(mmi_a, c='r', lw=2.)
        ax.axhline(mmi_a, c='r', lw=2.)
        ax.plot([2,9], [2,9], c='grey', lw=0.5)
        ax.set_xlim(2, 9)
        ax.set_ylim(2, 9)
        for cat in ['TN', 'FP', 'FN']:
            ax.scatter([obs[s]['max'] for s in alert_cats[mmi_a][cat]], 
                [max(alerts[s]['pred']) for s in alert_cats[mmi_a][cat]],
                c=cols[cat], label=cat, edgecolor='k', lw=0.5)
        ax.scatter([obs[s]['max'] for s in alert_cats[mmi_a]['TPL']], 
                [max(alerts[s]['pred']) for s in alert_cats[mmi_a]['TPL']],
                c='yellow', label='TP timely < MMI_tw', edgecolor='k', lw=0.5)
        ax.scatter([obs[s]['max'] for s in alert_cats[mmi_a]['TPU']], 
                [max(alerts[s]['pred']) for s in alert_cats[mmi_a]['TPU']],
                c='black', label='TP untimely', edgecolor='k', lw=0.5)
        cb = ax.scatter([obs[s]['max'] for s in alert_cats[mmi_a]['TPT']], 
                [max(alerts[s]['pred']) for s in alert_cats[mmi_a]['TPT']],
                c=[obs[s][mmi_tw]-alerts[s][mmi_a] for s in alert_cats[mmi_a]['TPT']], 
                cmap=win, label='TP timely', edgecolor='k', lw=0.5)
        if bTitles:
            cbar = fig.colorbar(cb, ax=ax)
            cbar.set_label('warning time (s)')
            ax.set_title(f'Maximum predicted MMI\nLatency: {latency}s, Mag: {mag_w}\nMMI_tw: {mmi_tw}, MMI_alert: {mmi_a}')
            #fig.legend(loc='upper left')
        ax.set_xlabel('Observed MMI')
        ax.set_ylabel('Predicted MMI')
        ax.grid()
        fig.savefig(os.path.join(evid, f'{evid}_mmi{mmi_a}_scatter.png'))
    plt.close()
    return

def plotScatterWarningTimeDist(evid, mmi_tw, mag_w, alert_cats, alerts, obs):
    '''
    Scatter plot of warning time against distance
    '''
    # MMI bounds
    mmimin = 2.
    mmimax = 10.
    cmap = plt.get_cmap('jet')
    norm = mpl.colors.Normalize(vmin=mmimin, vmax=mmimax)
    scalarMap = cm.ScalarMappable(norm=norm, cmap=cmap)
    cols = {'TN': 'white', 'FN': 'red', 'FP': 'orange'}
    for mmi_a in alert_cats:
        plt.clf()
        fig, ax = plt.subplots(1, 1, figsize=(8,5))
        for cat in ['TN', 'FP', 'FN']:
            ax.scatter([alerts[s]['dist'] for s in alert_cats[mmi_a][cat]],
                [0. for s in alert_cats[mmi_a][cat]], 
                c=cols[cat], s=100., label=cat, edgecolor='k', lw=0.5)
            ax.scatter([alerts[s]['dist'] for s in alert_cats[mmi_a][cat]],
                [0. for s in alert_cats[mmi_a][cat]], 
                c=[obs[s]['max'] for s in alert_cats[mmi_a][cat]], 
                cmap=cmap, vmin=mmimin, vmax=mmimax, label=cat, lw=0.5)
        ax.scatter([alerts[s]['dist'] for s in alert_cats[mmi_a]['TPL']], 
                [(obs[s]['location']['epidist']/3.5)-alerts[s][mmi_a] for s in alert_cats[mmi_a]['TPL']], 
                c='yellow', s=100., label='TP timely < MMI_tw', edgecolor='k', lw=0.5)
        ax.scatter([alerts[s]['dist'] for s in alert_cats[mmi_a]['TPL']], 
                [(obs[s]['location']['epidist']/3.5)-alerts[s][mmi_a] for s in alert_cats[mmi_a]['TPL']], 
                c=[obs[s]['max'] for s in alert_cats[mmi_a]['TPL']], 
                cmap=cmap, vmin=mmimin, vmax=mmimax, label='TP timely < MMI_tw', lw=0.5)
        ax.scatter([alerts[s]['dist'] for s in alert_cats[mmi_a]['TPU']], 
                [obs[s][mmi_tw]-alerts[s][mmi_a] for s in alert_cats[mmi_a]['TPU']], 
                c='k', s=100., label='TP untimely', edgecolor='k', lw=0.5)
        ax.scatter([alerts[s]['dist'] for s in alert_cats[mmi_a]['TPU']], 
                [obs[s][mmi_tw]-alerts[s][mmi_a] for s in alert_cats[mmi_a]['TPU']], 
                c=[obs[s]['max'] for s in alert_cats[mmi_a]['TPU']], 
                cmap=cmap, vmin=mmimin, vmax=mmimax, label='TP untimely', lw=0.5)
        cb = ax.scatter([alerts[s]['dist'] for s in alert_cats[mmi_a]['TPT']], 
                [obs[s][mmi_tw]-alerts[s][mmi_a] for s in alert_cats[mmi_a]['TPT']], 
                c=[obs[s]['max'] for s in alert_cats[mmi_a]['TPT']], 
                cmap=cmap, vmin=mmimin, vmax=mmimax, label='TP timely', edgecolor='k', lw=0.5)
        if bTitles:
            cbar = fig.colorbar(scalarMap, ax=ax)
            cbar.set_label('Observed MMI')
            ax.set_title(f'Warning time to MMI_tw or S-wave\nLatency: {latency}s, Mag: {mag_w}\nMMI_tw: {mmi_tw}, MMI_alert: {mmi_a}')
        ax.axhline(0.)
        ax.set_ylabel('warning time (s)')
        ax.set_xlabel('distance (km)')
        ax.grid()
        fig.savefig(os.path.join(evid, f'{evid}_mmi{mmi_a}_timedist.png'), bbox_inches='tight')
    plt.close()
    return

def plotWarningTimeCDF(evid, mmi_tw, mag_w, alert_cats, alerts, obs):
    '''
    Plot CDF of warning times
    '''
    # Warning time bounds
    wtmin = -100.
    wtmax = 300.
    wtstep = 1.
    # MMI bounds
    mmimin = 2.
    mmimax = 10.
    mmistep = 1.
    # Colours
    cmap = plt.get_cmap('jet')
    norm = mpl.colors.Normalize(vmin=mmimin, vmax=mmimax)
    scalarMap = cm.ScalarMappable(norm=norm, cmap=cmap)
    for mmi_a in alert_cats:
        plt.clf()
#        fig, ax = plt.subplots(1, 1, figsize=(10,8))
        fig, ax = plt.subplots(1, 1, figsize=(5,5))
        bEmpty = True
        for mmi in arange(mmimin, mmimax, mmistep):
            allstns = [s for s in alert_cats[mmi_a]['TPT'] if obs[s]['max'] >= mmi and obs[s]['max'] < mmi + mmistep]
            allstns.extend([s for s in alert_cats[mmi_a]['TPL'] if obs[s]['max'] >= mmi and obs[s]['max'] < mmi + mmistep])
            if len(allstns) == 0:
                continue
            bEmpty = False
            data = [obs[s][mmi_tw]-alerts[s][mmi_a] if obs[s][mmi_tw] is not None else (alerts[s]['dist']/3.5)-alerts[s][mmi_a] for s in allstns]
            data.extend([-1. for s in alert_cats[mmi_a]['TPU'] if obs[s]['max'] >= mmi and obs[s]['max'] < mmi + mmistep])
            data.extend([-1. for s in alert_cats[mmi_a]['FN'] if obs[s]['max'] >= mmi and obs[s]['max'] < mmi + mmistep])
            count, bins_count = histogram(data, bins=arange(wtmin, wtmax+wtstep/2., wtstep))
            if sum(count) == 0:
                    continue
            #print(mmi_a, mmi, count, bins_count)
            count = flip(count)
            pdf = count / sum(count)
            cdf = cumsum(pdf)
            ax.plot(flip(bins_count[1:]), cdf, lw=3, c=scalarMap.to_rgba(mmi), label=f'n={len(data)}')
        if bEmpty:
            continue
        if bTitles:
            ax.set_title(f'Warning time to MMI_tw or S-wave\nLatency: {latency}s, Mag: {mag_w}\nMMI_tw: {mmi_tw}, MMI_alert: {mmi_a}')
            fig.legend(loc='upper right')
        ax.set_xlabel('Warning time (s)')
        ax.set_ylabel('Empirical CDF')
        ax.set_ylim(0., 1.)
        ax.set_xlim(100., 1.)
        #ax.set_xlim(wtmax, wtmin+wtstep)
        ax.set_xscale('log')
        ax.grid(which='both', ls=':')
        ax.yaxis.tick_left()
        dnorm = mpl.colors.BoundaryNorm([1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5, 8.5, 9.5, 10.5], cmap.N)
        cbar = fig.colorbar(mpl.cm.ScalarMappable(norm=dnorm, cmap=cmap), ticks=range(2,11), ax=ax)
        cbar.set_label('Maximum observed MMI')
        fig.savefig(os.path.join(evid, f'{evid}_mmi{mmi_a}_cdf.png'), bbox_inches='tight')
    plt.close()
    return

def rdAlertTbl(fname):
    alerts = {}
    with open(fname, 'r') as fin:
        for l in fin:
            stn = l.split()[0]
            lstr = eval(l.replace(stn,''))
            alerts[stn] = lstr
    return alerts

def rdExceedanceTbl(fname):
    obs = {}
    with open(fname, 'r') as fin:
        for l in fin:
            stn = l.split()[0]
            lstr = eval(l.replace(stn,''))
            obs[stn] = lstr
    return obs

def sortCategories(evid, obs, alerts, mmi_tw = 5.0):
    '''
    Sort results into categories: TP, FP, FN, TN. Account for untimely TP and TP with low ground motion
    Plot 
    '''
    mmi_alerts = sorted(set([mmi for stn in alerts for mmi in alerts[stn] if stn != 'times' and mmi not in ['location', 'dist', 'pred', 'epidist']]))
    alert_cats = {}
    for mmi_a in mmi_alerts:
        if mmi_a == 'pred':
            continue
        fout = open(os.path.join(evid, f'{evid}_mmi{mmi_a}.dat'), 'w')
        alert_cats[mmi_a] = {}
        for cat in ['FP', 'TPU', 'TPT', 'TPL', 'FN', 'TN']:
            alert_cats[mmi_a][cat] = []
        for stn in obs:
            # MMI observed to exceed mmi_a at site
            if obs[stn][mmi_a] is not None:
                # mmi_a alerted
                if mmi_a in alerts[stn]:
                    # TP
                    # TP and strong (mmi > mmi_tw)
                    if obs[stn][mmi_tw] is not None:
                        # Alert later than MMI strong (mmi_tw)
                        if alerts[stn][mmi_a] > obs[stn][mmi_tw]:
                            fout.write(f'{stn} TP untimely\n')
                            alert_cats[mmi_a]['TPU'].append(stn)
                        # Alert earlier than MMI strong (mmi_tw)
                        else:
                            wt = obs[stn][mmi_tw]-alerts[stn][mmi_a]
                            fout.write(f'{stn} TP with warning time {wt}\n')
                            alert_cats[mmi_a]['TPT'].append(stn)
                    # TP but weak (mmi < mmi_tw)
                    else:
                        fout.write(f'{stn} TP but light (MMI < {mmi_tw})\n')
                        alert_cats[mmi_a]['TPL'].append(stn)
                # mmi_a not alerted
                else:
                    fout.write(f'{stn} FN\n')
                    alert_cats[mmi_a]['FN'].append(stn)
            # MMI not observed to exceed mmi_a at site
            else:
                # mmi_a alerted but mmi_a never reached
                if mmi_a in alerts[stn]:
                    fout.write(f'{stn} FP\n')
                    alert_cats[mmi_a]['FP'].append(stn)
                # mmi_a not alerted and mmi_a never reached
                else:
                    fout.write(f'{stn} TN\n')
                    alert_cats[mmi_a]['TN'].append(stn)
        fout.close()
    return alert_cats

if __name__ == '__main__':
    ###
    ### Input parameters ###
    ###
    evid = sys.argv[1] # GeoNet event ID
    mmi_tw = float(sys.argv[2]) # Target MMI to provide warning for, onset of damage
    mag_w = float(sys.argv[3]) # Magnitude to issue warnings for
    latency = float(sys.argv[4]) # Delivery latency
    ###
    ### Input parameters ###
    ###
    print(f'{evid} {mmi_tw} {mag_w} {latency}')

    ofname = os.path.join(evid, 'exceedance_times.tbl')
    if not os.path.isfile(ofname):
        print(f'Cannot create plots as file {ofname} is missing')
        exit()

    afname = os.path.join(evid, f'alert_times_{mag_w:.1f}_{latency:.0f}.tbl')
    if not os.path.isfile(afname):
        print(f'Cannot create plots as file {afname} is missing')
        exit()

    obs = rdExceedanceTbl(ofname)
    if not os.path.isfile(os.path.join(evid, f'{evid}_map-obs.png')):
        plotObsMaps(evid, obs)
    if not os.path.isfile(os.path.join(evid, f'{evid}_map-obs-zoom.png')):
        plotObsMaps(evid, obs, zoom=True)
    alerts = rdAlertTbl(afname)
    alert_cats = sortCategories(evid, obs, alerts, mmi_tw)
    plotMaps(evid, mmi_tw, mag_w, latency, alert_cats, alerts, obs)
    plotMaps(evid, mmi_tw, mag_w, latency, alert_cats, alerts, obs, zoom=True)
    plotScatterMMI(evid, mmi_tw, mag_w, alert_cats, alerts, obs)
    plotWarningTimeCDF(evid, mmi_tw, mag_w, alert_cats, alerts, obs)
    plotScatterWarningTimeDist(evid, mmi_tw, mag_w, alert_cats, alerts, obs)

