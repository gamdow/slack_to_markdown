from .slack import Export
from .markdown import MessageParser
from .progress import bar as pbar
from collections import defaultdict
from datetime import datetime

seconds_in_day = 60 * 60 * 24


def get_user_names(zip_path):
    archive = Export(zip_path)
    return archive.user_names


def get_channel_names(zip_path):
    archive = Export(zip_path)
    return archive.channel_names


def convert(zip_path, start_date=None, end_date=None, my_user_name=None, users=None, channels=None, asset_path='assets'):
    """
    Parameters
    ----------
    zip_path : str
        Path to zipped Slack export file
    start_date, end_date : (3,) array_like, optional
        Limit the date range. :math:`(year, month, day)`
    my_user_name : str, optional
        Will not treat this users messages as quotes, but rather as paragraphs (i.e. for the purpose of an individuals log). Can be any id used by Slack (e.g. display name, user name, real name, etc.)
    users, channels : array_like, str, optional
        Limit the users and channels to those listed. Use :py:func:`~slack_exporter.get_user_names` and :py:func:`~slack_exporter.get_channel_names` to get a full listing
    asset_path : str, optional
        Local path for downloaded assets

    Examples
    --------
    >>> sc.convert("Slack export.zip", start_date=(2018,1,1), end_date=(2019,1,1), my_user_name='alice', users=['alice','bob','carol'], channels=['general'])
    """

    print('Loading archive...', end='')
    archive = Export(zip_path, start_date=start_date, end_date=end_date, my_user_name=my_user_name, users=users, channels=channels)
    parser = MessageParser(archive.user_id_map, archive.my_user_id, asset_path=asset_path)
    print('done\n')

    print('Selected Options:')
    print('\tChannels:', archive.channel_names)
    print('\tUsers:', archive.user_names)
    print('\tPrimary User:', archive.primary_user)
    print('\tDate range:', archive.start_date, 'to', archive.end_date)

    print('\nConverting messages to markdown and downloading assets...')
    log = defaultdict(dict)
    for channel, msg in pbar(archive.yield_messages(), archive.num_messages()):
        md = parser.parse(msg)
        if md != "":
            ts = msg.timestamp
            days = int(ts // seconds_in_day)
            seconds = ts - days * seconds_in_day
            log[days][seconds] = (channel, md)

    filename = '{}_{}_{}.md'.format(archive.primary_user, archive.start_date, archive.end_date)

    print('\nWriting messages to {}...'.format(filename))
    with open(filename, 'w') as file:
        list = [(day, *log[day][seconds]) for day in sorted(log) for seconds in sorted(log[day])]
        last_day = None
        for day, channel, line in pbar(list, len(list)):
            if last_day != day:
                date = datetime.fromtimestamp(day * seconds_in_day)
                file.write('# ' + str(date.date()) + '\n')
                last_day = day
                last_channel = None
            if channel != last_channel:
                file.write('### ' + channel + '\n')
                last_channel = channel
            file.write(line + '\n')
