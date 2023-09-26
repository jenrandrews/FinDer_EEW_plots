# FinDer_EEW_plots
Create EEW performance plots for FinDer NZ. The performance metrics are computed following Meier and
assume a radial alert for MMI thresholds.

## Running
The run.sh script is the entry point and should be edited to give:
 * evid: the GeoNet event ID
 * fd_evid: the FinDer event ID
 * fd_auth: the FinDer author (pipeline)
 * alert_method: the desired mag + mmi -> alert distance (fixed vs30) table file to use
 * mmi_tw: the MMI warning time threshold to be used, usually set as the onset of damage

Create the directory <evid> for input and output files.

The alert_method file should be present in the same directory and be formatted as:
```
magnitude mmi distance
```
with distance in km, and computed for the exact mmi given. I have been computing for a single fixed vs30 and for the median MMI.

The file fd_evid.xml should be present in the <evid> directory, and is the database dump of SeisComP FinDer solutions.

## Scripts
 * ms2mmi.py: uses the GeoNet event ID to download the event data, station inventory data and miniseed files. It then creates the exceedence_times.tbl file. The exceedence_times contains the times that each station exceeds MMI levels, on a per-channel basis. MMI is computed using a gmice that should be specified at the top of the file, and is based on PGA and PGV. The table also contains the maximum recorded channel MMI for a station.
 * alert_times.py: uses the FinDer performance to compute EEW alerts for different MMI levels and creates the alert_times.tbl file. Alerts for a station site are based on comparing alert distances (input table, mag + mmi -> distance for fixed vs30) with the finite-fault to station distance. The earliest time that a site would be alerted for each MMI threshold is saved. The file also contains predicted MMIs for the station at each FinDer solution, as well as the times of the FinDer solutions.
 * plots.py: creates the EEW performance plots.
 * eew_utils.py: utilities for obspy event, station and waveform downloads.
 * moratalla.py: Moratalla et al. GMICE equations.

## EEW Metrics and Plots
EEW metrics are computed at station locations by comparing observed and predicted ground motions through time. Metrics are computed for all possible alert thresholds (mmi_a) and a single MMI of interest (mmi_tw). Station sites are categorised as:
 * TPT: a timely alert was issued, giving a warning time computed as the time MMI_tw is first observed at a station (single channel) minus the time a station receives an alert for MMI_a.
 * TPL: a timely alert was issued, but the observed maximum MMI is below MMI_tw.
 * TPU: an alert was issued by arrived after the site observed mmi_tw.
 * FP: an alert was issued for mmi_a but the observed maximum MMI is below mmi_a.
 * FN: an alert was not issued for mmi_a but the observed maximum MMI is above mmi_a.
 * TN: an alert was not issued for mmi_a and the observed maximum MMI was below mmi_a.

Plots created:
 * Maps: 
   * <evid>_mmi<mmi_a>_map.png and <evid>_mmi<mmi_a>_map-zoom.png: maps with stations coloured by alert category, or by warning time for TPT alerts. The zoom version is +/- 1 degree around the epicenter.
   * <evid>_map-obs.png and <evid>_map-obs-zoom.png: maps with stations coloured by maximum observed MMI.
 * Scatter:
   * <evid>_mmi<mmi_a>_scatter.png: scatter plots of maximum observed against maximum predicted MMI, with symbols coloured by alert category, or by warning time for TPT alerts.
 * CDF (cumulative density function):
   * <evid>_mmi<mmi_a>_cdf.png: CDF against warning time for alerts grouped by MMI for TPT and TPL alerts.
