import os
import urllib.request as urlr

max_text_file_lines = 10
# pandoc markdown treats newlines as spaces unless  there are multiple spaces before it (https://rmarkdown.rstudio.com/authoring_pandoc_markdown.html%23raw-tex)
newline = '  \n'


class MarkdownMessage():
    def __init__(self):
        self._msg = ""
        self._prefix = ""

    @property
    def string(self):
        return self._msg

    @property
    def line_prefix(self):
        return self._prefix

    @line_prefix.setter
    def line_prefix(self, v):
        self._prefix = v

    def sub_html_entities(self):
        self._msg = self._msg.replace('&gt;', '>')
        self._msg = self._msg.replace('&lt;', '<')

    def sub_ids_with_realname(self, id_map):
        for i, u in id_map.items():
            self._msg = self._msg.replace('<@' + i + '>', '@' + u + ':')

    def newline(self, num=1):
        for _ in range(num):
            self._msg += newline

    def add(self, string):
        self._msg += self._prefix
        self._msg += string


class Downloader():
    def __init__(self, asset_path):
        self._asset_path = asset_path
        self._handled_filetypes = {
            'image': self.download_image,
            'text': self.download_text}
        if not os.path.exists(asset_path):
            os.mkdir(asset_path)

    def download(self, file):
        request = urlr.Request(file)
        response = urlr.urlopen(request)
        return response.read()

    def download_image(self, file, md):
        filename = "-".join(file.permalink.split('/')[-3:])
        filepath = os.path.join(self._asset_path, filename)
        if not os.path.exists(filepath):
            data = self.download(file.url_private)
            with open(filepath, 'wb') as f:
                f.write(data)
        md.add('![' + file.permalink + '](' + filepath + ')')

    def download_text(self, file, md):
        md.add('[' + file.permalink + '](' + file.permalink + '):')
        data = self.download(file.url_private).decode('utf-8').split('\n')
        for l in data[:max_text_file_lines]:
            md.newline()
            md.add('> ' + l)
        rem = len(data) - max_text_file_lines
        if rem > 0:
            md.newline()
            md.add('> ... *({} lines remaining)*'.format(rem))

    def parse_and_download(self, file, md):
        if file.filetype in self._handled_filetypes:
            self._handled_filetypes[file.filetype](file, md)
            md.newline()
        elif file.is_available():
            md.add('[' + file.permalink + '](' + file.permalink + ')')
            md.newline()


class MessageParser():
    def __init__(self, user_id_map, my_user_id, asset_path='assets'):
        self._downloader = Downloader(asset_path)
        self._user_id_map = user_id_map
        self._my_user_id = my_user_id

    def download(self, url, md):
        self._downloader.parse_and_download(url, md)

    def parse(self, msg):
        md = MarkdownMessage()

        if msg.is_user_message():
            if self._my_user_id is None or msg.user_id != self._my_user_id:
                # markdown bold
                md.add("**" + self._user_id_map[msg.user_id] + "**:")
                if msg.num_lines + msg.num_files > 1:
                    md.newline(2)
                    # markdown quote
                    md.line_prefix = '> '
                else:
                    md.add(' ')

            for line in msg.yield_lines():
                if line.startswith('• '):
                    # convert slack list to markdown list
                    md.add(line.replace('• ', '* ', 1))
                elif line.find('# ') < 5:
                    # downgrade heading size
                    md.add(line.replace('# ', '## ', 1))
                else:
                    md.add(line)
                md.newline()

        md.sub_ids_with_realname(self._user_id_map)

        for f in msg.yield_files():
            self._downloader.parse_and_download(f, md)

        md.sub_html_entities()

        return md.string
