"""
sudep is a mudule for importing and organizing data from the SUDEPmonitor
database. Primarily, list user_list and functions: get_user() and plot() should
be the only objects needed for use of this module. The remaining functions are
public incase additional functionallity is desired. It may also be beneficial to
view the help for classes User, Session, and Profile to better understand how
the data is structured.

Example 3: Viewing a summary of all of user's collected data.
    >>> SM8 = get_user(user_list[7])
    >>> print(SM8)

Example 2: Getting heart rate and accelerometer data from a user's session.

    >>> user = get_user(user_list[0])
    >>> session = user.session[user.dates[0]]
    >>> heart_data = session.heart_data
    >>> accel_data = session.accel_data
    >>> plot(session)

Both heart_data and accel_data are dictionaries of numpy arrays (see Session
for more information). The last line plots the accelerometer data and heart
rate from over the duration of the session.

Example 3: Manually getting a selection of sessions from a user.
    >>> user = user_list[0]
    >>> user_sessions = get_session_dates_for(user)
    >>> # Returns an array containing all session dates for the given user.
    >>> sessions = user_sessions[0:2]
    >>> data = get_session_for(user,sessions)
    >>> # Returns a dictionary containing all the data for the given sessions.

By leaving out the optional parameter session in get_session_for() a dictionary
containing data from all of that user's sessions would be returned.

Note: The data from Example 3 can be obtained much more succinctly using:
    >>> user = get_user[user_list[0]]
    >>> data = user.session[user.dates[0:2]]

"""

__all__ = ['user_list','get_user','save','load','User','Session','Profile',
           'get_events_for','get_profile_for','get_session_dates_for',
           'get_session_for','plot']

__version__ = '0.1'
__author__ = 'David Connell'

import requests
import matplotlib.pyplot as plt
import numpy as np
import cPickle
import os

### Download from database ###
base_url = 'https://sudepmonitor.firebaseio.com/'

def get_user_list():
    url = base_url + 'UserList.json'
    return download_json_data_from(url)

def download_json_data_from(url):
    json_data = requests.get(url)

    if json_data.json() == None:
        return {}

    return json_data.json()

user_list = get_user_list()

### Get user ###
def get_user(user_name, reload=False):
    """ Returns a class instance of type User for user_name. The User is loaded
    if it exists locally. Otherwise the User is downloaded from the database
    then saved locally in the directory 'current_path/Users'. To update a User
    that is saved set the optional parameter reload=True. """

    _look_for_and_create_users_folder()

    if _is_file_in_directory(user_name) and not reload:
        return(load(user_name))

    elif user_name in user_list:
        user = User(user_name)
        save(user)
        return(user)

    else:
        print('%s does not exist in the database' %user_name)
        return

def _look_for_and_create_users_folder():
    """ Looks for the folder "Users" in the current directory and makes it
    if it does not exist. """

    dir_path = 'Users'
    if not os.path.exists(dir_path):
        print('Making')
        os.makedirs(dir_path)

def _is_file_in_directory(name):
    file_name = name + '.pkl'
    file_list = os.listdir('Users')

    if file_name in file_list:
        return True
    else:
        return False


def save(user,update=True):
    """ Saves instances of the class User via pickle to prevent the need of
    the slow process of redownloading the data from the server everytime a
    file is run. Files are saved as the user_name (UserID) in folder Users.

    Optional parameter update can be used to specify if you want to update
    a user if the user has already been saved. If True pickle will right over
    the old file otherwise the save call will be ignored."""

    _look_for_and_create_users_folder()
    file_path = 'Users/' + user.user_name + '.pkl'

    if update == False:
        if _is_file_in_directory(user.user_name):
            return

    file = open(file_path, 'wb')
    cPickle.dump(user,file,protocol=2)

def load(user_name):
    """ loads previously saved files. Files are saved as the user_name (UserID).
    Input user_name should be a string. """

    file_path = 'Users/' + user_name + '.pkl'
    file = open(file_path, 'rb')
    return(cPickle.load(file))

### Data structures ###
class User:
    """ User holds all the information for a given user. User is called with
    User(user_name) where user_name is a string that can be obtained from
    user_list. User contains attributes: .user_name,.profile,.events,
    .sessions, and .dates. Print User to see a summary of all the user's
    information.

    .profile is of type custom class Profile and .sessions is a dictionary of
    type custom class Session. See Profile and Session for more information.

    .events is a dictionary containing all the user's events with the dates of
    the events as the keys.

    .dates is a list of dates for each of the user's sessions and can be used
    as the keys for the .sessions dictionary.

    ex: SM18 = User('SM18')
        first_session = SM18.sessions(SM18.dates[0])

    Which returns a session dictionary described by the custom class Session.
    However, all the data for the user is downloaded from the database everytime
    User() is called. To reduce the number time consuming downloads it is
    suggested to get instances of User through the function get_user(user_name)
    instead which, manages saving and loading user data to and from a local
    drive. """

    def __init__(self,name):
        self.user_name = name
        self.profile = Profile(name)
        self.events = get_events_for(name,event_type=True)
        self.sessions = get_session_for(name)
        self.dates = get_session_dates_for(name)

    def __str__(self):
        user_name = 'User Name: %s \n' %(self.user_name)
        profile = self._profile_string()
        events = self._event_string()
        sessions = self._session_string()
        return(user_name + profile + events + sessions)

    def _profile_string(self):
        profile = self.profile.__str__()
        return('Profile: \n %s \n' %profile)

    def _event_string(self):
        string = ""
        for event,types in self.events.items():
            lexed_event = _lex(event)
            string += '\t %s || %s \n' %(lexed_event,types)
        return('Events (onset (dd.MM.yy hh:mm:ss) || event type): \n' + string + '\n')

    def _session_string(self):
        string = ""
        keys = _date_sort(self.sessions.keys())
        for key in keys:
            duration = self._ss_to_hhmmss(self.sessions[key].duration)
            lexed_session = _lex(key)
            string += '\t %s || %s \n' %(lexed_session,duration)
        return('Sessions (date (dd.MM.yy hh:mm:ss) || duration): \n' + string + '\n')

    def _ss_to_hhmmss(self,time_in_secs):
        hours = float(time_in_secs)/3600.0
        mins = hours - int(hours)
        mins *= 60
        secs = mins - int(mins)
        secs *= 60
        return('%02i:%02i:%02i' %(int(hours),int(mins),int(secs)))

    def __repr__(self):
        return self.__str__()

class Profile:
    """ A class for presenting the profile data for a user. """

    def __init__(self,name):
        profile = get_profile_for(str(name))
        self.dob = profile['Date of Birth']
        self.gender = profile['Gender']
        self.height = profile['Height (m)']
        self.weight = profile['Weight (kg)']

    def __str__(self):
        dob = '\t Date of Birth: %s \n' %self.dob
        gender = '\t Gender: %s \n' %self.gender
        height = '\t Height: %s m \n' %self.height
        weight = '\t Weight: %s kg \n' %self.weight
        return(dob + gender + height + weight)

    def __repr__(self):
        return self.__str__()


def get_profile_for(user_list):
    """ Gets profiles for the selected users. users can be a single user, a
    list of users, or 'all' to return all profiles on database. """

    if user_list == 'all':
        user_list = globals()['user_list']

    elif type(user_list) == str:
        user = user_list
        return _get_individual_profile_for(user)

    profiles = {}
    for user in user_list:
        profiles[user] = _get_individual_profile_for(user)

    return profiles

def _get_individual_profile_for(user):
    url = base_url + user + '/MetaData/Profile.json'
    profile = download_json_data_from(url)

    if profile == None:
        return {}

    return profile


def get_events_for(user, event_type=False):
    """ Produces all events for the given user. If optional paramerer eventType
    is set to True both the date and event type are returned otherwise only the
    date is returned. """

    url = base_url + user + '/MetaData/Events.json'
    if not event_type:
        url += '?shallow=true'

    user_events = download_json_data_from(url)

    if event_type:
        return user_events
    else:
        return user_events.keys()


class Session:
    """ Session is a class for organizing the data from a user's session.
    Session contains the attributes .accel_sampling_freq, .duratoin,
    .accel_data, and .heart_data.

    .accel_sampling_freq is the sampling frequency of the accelerometer during
    the recording.

    .duration is  the elapsed time of the session in seconds.

    .accel_data is a dictionary containing three numpy arrays, one for
    accelerometer data in each of the spacial axes: 'x', 'y', and 'z'.

    .heart_data is a dictionary containing a 'times' numpy array storing the time
    since the start of the session for each heartrate datum and a 'heart_rate'
    numpy array with the heart rate data. """

    def __init__(self,session):
        self.accel_sampling_freq = session['Accelerometer sampling frequency']
        self.duration = session['Duration']
        self.accel_data = self._convert_accel_data_to_array_for(session)
        self.heart_data = self._convert_heart_data_to_array_for(session)

    def _convert_accel_data_to_array_for(self,session):
        if 'Accelerometer data' in session:
            accel = session['Accelerometer data']
        else:
            return 'Empty'

        x = np.array(accel['x'])
        y = np.array(accel['y'])
        z = np.array(accel['z'])

        return({'x':x,'y':y,'z':z})

    def _convert_heart_data_to_array_for(self,session):
        if 'Heartrate data' in session:
            heart_data = session['Heartrate data']
        else:
            return 'Empty'

        times = np.array(heart_data['Times'])
        heart_rate = np.array(heart_data['Heartrate'])

        return({'times':times,'heart_rate':heart_rate})

    def __str__(self):
        fs = '\t Accelerometer sampling frequency: %s samples/s \n' %self.accel_sampling_freq
        duration = '\t Elapsed time of session: %0.2f s \n' %float(self.duration)

        print(self.heart_data)
        heart_rate = self.heart_data['heart_rate']

        avg_heart_rate = '\t Average heart rate: %0.2f bpm \n' %(np.mean(heart_rate))
        return(fs + duration + avg_heart_rate)

    def __repr__(self):
        return self.__str__()


def get_session_for(user,sessions='all'):
    """ optional sessions parameter should be a string containing the name of
    one of the users sessions, default 'all' for all the users sessions, or a
    list containing a subset of the users sessions.

    Example 1: get_data_for('SM9','07071720045')
    Example 2: get_data_for('SM11',['070717004643', '070717004604', '070717004715'])
    Example 3: get_data_for(user_list[3])

    Results are of type custom class Session. """

    if sessions == 'all':
        sessions = get_session_dates_for(user)

    if type(sessions) is list:
        user_data = {}
        for session in sessions:
            user_data[session] = _get_single(session,user)
        return user_data

    else:
        return(_get_single(sessions,user))

def get_session_dates_for(user,readable=False):
    """ if optional parameter readable is True the dates will be returned in
    an easier to read format: dd.MM.yy hh:mm:ss. Otherwise the date is
    returned: ddMMyyhhmmss. The later form must be used in order to be passed
    into get_session_for(). """

    url = base_url + user + '.json?shallow=true'
    user_dates = download_json_data_from(url)

    del user_dates['MetaData']

    if readable:
        return _lex_multiple(user_dates)
    else:
        return _date_sort(user_dates.keys())

def _get_single(session,for_user):
        url = base_url + for_user + '/' + session + '.json'
        return Session(download_json_data_from(url))


def _lex_multiple(dates):
    dates = dates.keys()
    lexed_dates = []
    for date in dates:
        lexed_date = _lex(date)
        lexed_dates.append(lexed_date)
    return _date_sort(lexed_dates)

def _lex(date):
        characters = ['.','.',' ',':',':','']
        lexed_date = ""
        for iChar in range(0,len(characters)):
            iDate = iChar*2
            lexed_date += (date[iDate:(iDate+2)] + characters[iChar])
        return(lexed_date)

def _date_sort(dates):
    """ Sorts a list of dates in increasing order by year, month, day, hour,
    minute, then second i.e most recent last. """

    dates.sort(key=lambda x: (x[4:6],x[2:4],x[0:2],x[6:8],x[8:10],x[10:12]))
    return(dates)

### Plot ###
def plot(session):

    def plot_accel():
        x = session.accel_data['x']
        y = session.accel_data['y']
        z = session.accel_data['z']

        end = float(session.duration)
        t = _linspace(0,end,len(x))

        ax = fig.add_subplot(211)
        plt.plot(t,x,label='X')
        plt.plot(t,y,label='Y')
        plt.plot(t,z,label='Z')
        ax.set_ylabel('Acceleration (G)')
        ax.set_title('Accelerometer Data')
        plt.legend()
        ax.get_xaxis().set_visible(False)
        return ax

    def plot_heart_rate():
        heart_rate = session.heart_data['heart_rate']
        times = session.heart_data['times']
        ax = fig.add_subplot(212, sharex=ax1)
        plt.plot(times,heart_rate)
        ax.set_xlabel('time (s)')
        ax.set_ylabel('Heart rate (BPM)')
        ax.set_title('Heart Rate')
        return ax

    fig = plt.figure()
    ax1 = plot_accel()
    ax2 = plot_heart_rate()


def _linspace(start,end,stepsize):
    start = float(start); end = float(end); length = float(stepsize)
    out = np.linspace(start,end,length)
    return(out)
