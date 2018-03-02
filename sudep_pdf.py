from sudep import *
import sudep_HRV
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import laplace
import math

### Select sessions and plot types. ###
use_long_sessions = True
do_detect = True
do_plot_accel = True
do_plot_beat = False
do_make_table = True
accel_hist_window = 1   # Window size (in data points) for the moving average
                        # used on the accelerometer difference signal when
                        # creating the histogram.

me = get_user('SM36')
long_sessions = [me.dates[3],me.dates[6],me.dates[8]]
short_sessions = [me.dates[1],me.dates[2],me.dates[4],me.dates[7]]

if use_long_sessions:
    dates = long_sessions
else:
    dates = short_sessions

session_list = [me.sessions[date] for date in dates]


def plot_accel_diff_hist_for(session,window=1):
    accel_data = np.array(unpack_accel_from(session))
    accel_diff = np.diff(accel_data,axis=1)

    if window > 1:
        accel_diff = moving_average(accel_diff,window)

    names = ('x','y','z')

    fig, axes = plt.subplots(1,3,sharey=True,sharex=True)
    all_dimesions_hist(accel_diff,axes,names)

    fig.suptitle('Laplace PDF fit to change in acceleration',fontsize=16)
    axes[0].set_ylabel('Probability')
    axes[2].set_xlabel('Change in acceleration (G)',labelpad=12,fontsize=10)

def unpack_accel_from(session):
    accel_data = session.accel_data
    x = accel_data['x']
    y = accel_data['y']
    z = accel_data['z']
    return(x,y,z)

def moving_average(signal,n):
    indices = np.mgrid[0:int(math.floor(len(signal[0])/n)),0:n]
    indices = np.transpose(np.sum(indices,axis=0))
    signal = np.mean(signal[0:,indices],axis=1)
    return(signal)

def all_dimesions_hist(data,axes,names):
    for i in xrange(len(names)):
        signal = data[i]; ax = axes[i]; name = names[i]

        lim = np.percentile(signal,99)
        bins = np.linspace(-lim,lim,40)

        accel_diff_hist(signal,ax,name,lim,bins)
        plot_laplace_dist(signal,ax,lim,bins)

def accel_diff_hist(signal,ax,name,xlim,bins):
    ax.hist(signal,bins=bins,normed=True)
    ax.set_xlim(xmin=-xlim,xmax=xlim)
    ax.get_xaxis().get_major_formatter().set_scientific(True)
    ax.get_xaxis().get_major_formatter().set_powerlimits((0,1))
    ax.set_title('Dimension %s'%name,fontsize=12)

def plot_laplace_dist(signal,ax,lim,bins):
    (mu,sigma) = dist_stats(signal,lim)
    b = sigma/(2**0.5)
    ax.plot(bins,laplace.pdf(bins,mu,b),'r--')

def dist_stats(signal,lim):
    stat_signal = signal[abs(signal) < lim]
    mu = np.mean(stat_signal)
    sigma = np.std(stat_signal,ddof=1)
    return(mu,sigma)

def plot_beat_hist(session):
    """ Compares beat-interval histogram to Erlang distribution. Requires long
    sessions. """

    fig, ax = plt.subplots(1)

    signal = 1000.0*60.0/session.heart_data['heart_rate']
    bins = np.linspace(min(signal),max(signal),30)
    ax.hist(signal,bins=bins,normed=True)

    mu = np.mean(signal)
    plot_erlang(ax,mu)

    ax.set_xlabel('Beat-interval (ms)')
    ax.set_ylabel('Probability')
    ax.set_title(r'Erlang PDF with k = 55 and $\lambda$ = %0.4f fit to beat-interval histogram' %(50/mu))

def plot_erlang(ax,mu):
    x = np.linspace(0,1600,1000)

    erlang = lambda x,k,mu: np.multiply(np.power(x,k-1),np.exp(-x/mu))/((mu**k)*math.factorial(k-1))
    ax.plot(x,2.8*erlang(x,55,mu/50),'r--')

def variance_statistics(signal,window):
    var = windowed_sample_variance(signal,window)

    max_var = np.max(var)
    min_var = np.min(var)
    mean_var = np.mean(var)
    var_var = np.var(var)

    return(max_var,min_var,mean_var,var_var)

def windowed_sample_variance(signal,window):
    indices = np.mgrid[0:int(len(signal) - window + 1),0:window]
    indices = np.transpose(np.sum(indices,axis=0))
    var = np.var(np.diff(signal[indices]),axis=0)
    return(var)

def plot_accel_detection(session,num_seconds = 5):
    (x,y,z) = unpack_accel_from(session)
    freq = session.accel_sampling_freq
    time = np.linspace(0,float(len(x))/freq,len(x))
    num_points = num_seconds*freq

    plt.figure()
    plt.plot(time,x,label='x')
    plt.plot(time,y,'r',label='y')
    plt.plot(time,z,'g',label='z')

    mark_high_var(time,x,num_points)
    mark_high_var(time,y,num_points)
    mark_high_var(time,z,num_points)

    plt.ylim(ymax=10,ymin=-10)
    plt.xlabel('time (s)')
    plt.ylabel(r'Variance for accelerometer data ($G^2$)')
    plt.xlim(xmax=time[-1])
    plt.title('Accelerometer data')

    plt.legend()

def mark_high_var(time, signal, window):
    var = windowed_sample_variance(signal,window)

    buffer = np.zeros(window-1)
    is_above_thresh = np.append(buffer,find_high_variance(var)).astype(bool)

    plt.plot(time[is_above_thresh],signal[is_above_thresh],'k.')

def find_high_variance(var, THRESH=1):
    return(var > THRESH)

def make_vars_latex_table_in(file_name,vars):
    (x_vars,y_vars,z_vars) = vars

    mean_x_var = np.mean(x_vars,axis=0)
    mean_y_var = np.mean(y_vars,axis=0)
    mean_z_var = np.mean(z_vars,axis=0)

    out = np.array([mean_x_var,mean_y_var,mean_z_var])
    np.savetxt(file_name,out,delimiter=' & ',newline=' \\\\\n',fmt='%0.4e')

def save_vars(session,vars):
    (x,y,z) = unpack_accel_from(session)
    (x_vars,y_vars,z_vars) = vars

    x_vars.append(np.array(variance_statistics(x,40)))
    y_vars.append(np.array(variance_statistics(y,40)))
    z_vars.append(np.array(variance_statistics(z,40)))
    return(x_vars,y_vars,z_vars)

def __main__():
    x_vars = []; y_vars = []; z_vars = []
    vars = (x_vars, y_vars, z_vars)

    for session in session_list:
        if do_detect:
            plot_accel_detection(session)

        if do_plot_accel:
            plot_accel_diff_hist_for(session,window=accel_hist_window)

        if do_plot_beat:
            plot_beat_hist(session)

        if do_make_table:
            vars = save_vars(session,vars)

    plt.show()

    if do_make_table:
        make_vars_latex_table_in('AccelVarianceTable.tex',vars)

if __name__ == "__main__":
    __main__()
