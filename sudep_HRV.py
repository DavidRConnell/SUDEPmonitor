""" sudep_HRV produces plots for viewing heart rate variability in the form of
Lorenz plots and the related cardiac sympathatic index (CSI)[jeppesen2014using].
The module also provides the functions needed to calculate CSI_n, where n is
the number of sample points used. Commonly n is set to 30,50, or 100.

This module is intended to be used with the sudep module. Due to limitaions to
accesing the photoplethysmogram (PPG) of the Apple Watch, heart rate samples
are the average of many beats rather than individual beats making the CSI and
Lorenz plots approximations. """

import numpy as np
import matplotlib.pyplot as plt
import math

# From piskorski2007geometry.
def CSI(heart_data,num_points=50,from_watch=True):
    ''' Calculates the CSI of num_points. If from_watch is true the input is
    the heart_data from the Session class of sudep.py, otherwise heart_data
    is a vector of beat intervals. '''

    if from_watch:
        beats = 60.0/heart_data['heart_rate']
    else:
        beats = heart_data

    SD1,SD2 = SD(beats,num_points=num_points)

    SD2[SD1 == 0] = 1
    SD1[SD1 == 0] = 1

    return(SD2/SD1)


def SD(beats,num_points=50):
    ''' Calculates n SD1 and SD2 values for num_points of beats in a
    one point sliding window fashion.

    Where n = len(heartrate_signal) - num_points + 1 and heartrate_signal is
    a vector of beat intervals. '''

    signal_length = len(beats)
    n = signal_length - num_points + 1

    indices = np.sum(np.mgrid[0:n,0:num_points],axis=0)
    windowed_beats = beats[indices]

    x = windowed_beats[0:n-1]; y = windowed_beats[1:n]

    def means(x,y):
        meanx = np.mean(x,axis=1)
        meany = np.mean(y,axis=1)
        return(meanx,meany)

    meanx,meany = means(x,y)

    def SD1():
        mean = np.transpose([meany - meanx])

        SD1 = np.std((x - y) + mean,axis=1)/(2.0**0.5)
        return(SD1)

    def SD2():
        mean = np.transpose([meanx + meany])

        SD2 = np.std((x + y) - mean,axis=1)/(2.0**0.5)
        return(SD2)

    return(SD1(),SD2())

def HRV_plots(session,CSI_num=50):
    """ plots CSI_50, heartrate of time, and a lorenz plot. Input should be
    heart_data in a dictionary containing arrays for 'heartrate' and 'time'
    as is returned for an instance of Session.heart_data created from sudep."""

    heart_data = session.heart_data
    heart_rate = heart_data['heart_rate']
    beats = 60*1000/heart_rate
    times = heart_data['times']


    def plot_CSI_and_heart_rate(n = CSI_num):
        fig, (ax1,ax2) = plt.subplots(2,1,sharex='row')
        ax1 = plot_CSI(times,beats,n,ax=ax1)
        ax2 = plot_heart_rate(times,heart_rate,ax=ax2)

        ax1.set_title(r'Estimate of CSI$_{%i}$ during sleep' %n)
        ax2.set_title('Heartrate during sleep')
        fig.subplots_adjust(hspace=0.4)

    plot_CSI_and_heart_rate()

def plot_CSI(times, beats, n, ax=None):
    if ax is None:
        ax = plt.gca()

    SD1,SD2 = SD(beats,num_points=n)
    ax.plot(times[n:],SD2/SD1)
    ax.set_xlabel('time(s)')
    ax.set_ylabel(r'CSI$_{%i}$' %n)
    return ax

def plot_heart_rate(times, heart_rate, ax=None):
    if ax is None:
        ax = plt.gca()

    ax.plot(times,heart_rate)
    ax.set_xlabel('time(s)')
    ax.set_ylabel('Heart rate(bpm)')
    ax.set_xlim(xmax=times[-1])
    return ax

def plot_lorenz(beats,ax=None):
    if ax is None:
        ax = plt.gca()

    ax.plot(beats[0:-1],beats[1:],'.')
    ax.set_xlabel(r'$i_{th}$ beat-beat interval (s)')
    ax.set_ylabel(r'$i_{th}+1$ beat-beat interval (s)')
    return ax

def _lorenz_ellipse(beats):
    meanx = np.mean(beats[0:-1]); meany = np.mean(beats[1:])
    SD1,SD2 = SD(beats,num_points=len(beats)-1)
    SD2 = 4*SD2*np.max(beats)
    e = math.pi/4.0
    x1 = meanx - SD2*math.sin(math.pi/4.0); x2 = meanx + SD2*math.sin(math.pi/4.0)
    y1 = meany - SD2*math.cos(math.pi/4.0); y2 = meany + SD2*math.cos(math.pi/4.0)
    a = 0.5*math.sqrt((x2-x1)**2.0+(y2-y1)**2.0)
    b = a*math.sqrt(1.0-e**2)
    t = np.linspace(0,2*math.pi)
    X = a*np.cos(t)
    Y = b*np.sin(t)
    w = math.atan2(y2-y1,x2-x1)
    x = (x1+x2)/2.0 + X*math.cos(w) - Y*math.sin(w)
    y = (y1+y2)/2.0 + X*math.sin(w) + Y*math.cos(w)
    return(x,y)
