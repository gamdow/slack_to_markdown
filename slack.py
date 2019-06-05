import zipfile
import json
import os
from datetime import datetime


def format_timestamp(ts):
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d")


class File():
    def __init__(self, file_data):
        self._file_data = file_data

    @property
    def permalink(self):
        return self._file_data['permalink']

    @property
    def url_private(self):
        return self._file_data['url_private']

    @property
    def filetype(self):
        if 'mimetype' in self._file_data:
            return self._file_data['mimetype'].split('/')[0]
        else:
            return None

    def is_available(self):
        return 'permalink' in self._file_data


class Message():
    def __init__(self, msg_data):
        self._msg_data = msg_data

    @property
    def user_id(self):
        return self._msg_data['user'] if 'user' in self._msg_data else None

    @property
    def timestamp(self):
        return float(self._msg_data['ts'])

    @property
    def num_lines(self):
        return len(self.yield_lines())

    @property
    def num_files(self):
        return len(list(self.yield_files()))

    def is_user_message(self):
        return ('user' in self._msg_data) and ('subtype' not in self._msg_data)

    def yield_lines(self):
        return [l for l in self._msg_data['text'].split('\n') if l != ""]

    def yield_files(self):
        if 'files' in self._msg_data:
            for f in self._msg_data['files']:
                yield File(f)


class Archive():
    def __init__(self, archive, filename):
        self._data = json.load(archive.open(filename))

    @property
    def all_data(self):
        return self._data

    def find(self, value):
        for d in self._data:
            values = list(d.values())
            if 'profile' in d:
                values = values + list(d['profile'].values())
            if value in values:
                return d
        return None

    def filtered_values(self, key, in_values=None):
        if in_values is None:
            return set(c[key] for c in self._data)
        else:
            return set(self.find(v)[key] for v in in_values if self.find(v) is not None)


class Export():
    def __init__(self, zip_path, start_date=None, end_date=None, my_user_name=None, users=None, channels=None):
        self._archive = zipfile.ZipFile(zip_path, 'r')
        self._channels = Archive(self._archive, "channels.json")
        self._users = Archive(self._archive, "users.json")
        self._channel_names = self._channels.filtered_values('name', channels)
        # assert len(self._channel_names) > 0, "No channels selected!"
        self._user_names = self._users.filtered_values('name', users)
        # assert len(self._user_names) > 0, "No users selected!"
        self._user_ids = self._users.filtered_values('id', users)

        self._my_user_id = None
        if my_user_name is not None:
            user_data = self._users.find(my_user_name)
            if user_data is not None:
                self._my_user_id = user_data['id']

        min_ts = min(m.timestamp for _, m in self.yield_messages(True))
        if start_date is not None:
            self._start_ts = max(datetime(*start_date).timestamp(), min_ts)
        else:
            self._start_ts = min_ts

        max_ts = max(m.timestamp for _, m in self.yield_messages(True))
        if end_date is not None:
            self._end_ts = min(datetime(*end_date).timestamp(), max_ts)
        else:
            self._end_ts = max_ts

    @property
    def users_data(self):
        return self._users.all_data

    @property
    def user_id_map(self):
        return {u['id']: u['profile']['real_name'] for u in self.users_data}

    @property
    def my_user_id(self):
        return self._my_user_id

    @property
    def primary_user(self):
        return self.user_id_map[self._my_user_id] if self._my_user_id is not None else "slack"

    @property
    def user_names(self):
        return self._user_names

    @property
    def channel_names(self):
        return self._channel_names

    @property
    def start_date(self):
        return format_timestamp(self._start_ts)

    @property
    def end_date(self):
        return format_timestamp(self._end_ts)

    def message_in_range(self, msg):
        return msg.user_id in self._user_ids and msg.timestamp >= self._start_ts and msg.timestamp <= self._end_ts

    def yield_messages(self, ignore_range=False):
        for file_name in self._archive.namelist():
            channel = file_name.split(os.path.sep)[0]
            if channel in self._channel_names and file_name.endswith('.json'):
                file = json.load(self._archive.open(file_name))
                for m in file:
                    msg = Message(m)
                    if ignore_range or self.message_in_range(msg):
                        yield channel, msg

    def num_messages(self):
        return len(list(self.yield_messages()))
