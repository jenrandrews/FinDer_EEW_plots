from numpy import arange, where

def gm2mmiArray(log10pga=None, log10pgv=None):
    '''
    Input log10(ground motion) PGA (cm/s/s) and/or PGV (cm/s)
    Output MMI
    GMICE Moratalla et al (2021), eqn 3, table 2
    '''
    if log10pga is None and log10pgv is None:
        return None
    mmi = {}
    if log10pga is not None:
        mmi['pga'] = where(log10pga < 1.89137, 1.992 * log10pga + 1.7601, 3.9322 * log10pga - 1.9095)
    if log10pgv is not None:
        mmi['pgv'] = where(log10pgv < 1.0024, 1.6323 * log10pgv + 4.107, 3.837 * log10pgv + 1.897)
    if log10pga is None:
        mean_mmi = mmi['pgv']
    elif log10pgv is None:
        mean_mmi = mmi['pga']
    else:
        mean_mmi = (mmi['pga'] + mmi['pgv'])/2. # mean
    mean_mmi = where(mean_mmi < 2.0, 2.0, mean_mmi)
    mean_mmi = where(mean_mmi > 9.0, 9.0, mean_mmi)
    return mean_mmi

def gm2mmi(log10pga=None, log10pgv=None):
    '''
    Input log10(ground motion) PGA (cm/s/s) and/or PGV (cm/s)
    Output MMI
    GMICE Moratalla et al (2021), eqn 3, table 2
    '''
    if log10pga is None and log10pgv is None:
        return None
    mmi = {}
    if log10pga is not None:
        if log10pga < 1.89137:
            mmi['pga'] = 1.992 * log10pga + 1.7601
        else:
            mmi['pga'] = 3.9322 * log10pga - 1.9095
    if log10pgv is not None:
        if log10pgv < 1.0024:
            mmi['pgv'] = 1.6323 * log10pgv + 4.107
        else:
            mmi['pgv'] = 3.837 * log10pgv + 1.897
    if log10pga is None:
        mean_mmi = mmi['pgv']
    elif log10pgv is None:
        mean_mmi = mmi['pga']
    else:
        mean_mmi = (mmi['pga'] + mmi['pgv'])/2. # mean
    if mean_mmi < 2.0:
        mean_mmi = 2.0
    if mean_mmi > 9.0:
        mean_mmi = 9.0
    return mean_mmi

def mmi2gm(mmi):
    '''
    Input MMI
    Output PGA (cm/s/s) and PGV (cm/s)
    GMICE Moratalla et al (2021), eqn 3, table 2
    '''
    gm = {}
    if mmi < 5.52777:
        gm['pga'] = pow(10., (mmi-1.7601)/1.992)
    else:
        gm['pga'] = pow(10., (mmi+1.9095)/3.9322)
    if mmi < 5.7433:
        gm['pgv'] = pow(10., (mmi-4.107)/1.6323)
    else:
        gm['pgv'] = pow(10., (mmi-1.897)/3.837)
    return gm

def mmi2gmTBL():
    '''
    Create a dictionary with MMI as key and value as a dictionary of 'pga' (cm/s/s) and 'pgv' (cm/s)
    '''
    gm = {}
    for mmi in arange(2.5, 9.0, 0.5):
        gm[mmi] = mmi2gm(mmi)
    return gm

if __name__ == '__main__':

    #for mmi in [3.5, 5.0]:
    #    print(mmi, mmi2gm(mmi))

    from numpy import arange
    pga = arange(0.2, 2.7, 0.1)
    pgv = arange(-1., 1.7, 0.1)
    mmi_pga = gm2mmiArray(pga, None)
    mmi_pgv = gm2mmiArray(None, pgv)
    #mmi_mean = gm2mmiArray(pga, pgv)
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1,2)
    ax[1].plot(pga, mmi_pga)
    ax[1].set_xlabel('pga cm/s/s')
    ax[1].set_ylabel('mmi')
    ax[0].plot(pgv, mmi_pgv)
    ax[0].set_xlabel('pgv cm/s')
    ax[0].set_ylabel('mmi')
    #ax[2].plot(pga, mmi_mean)
    plt.savefig('moratalla.png')
