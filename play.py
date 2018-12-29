#!/usr/bin/env python3
"""
Play is a powerful command line Python media player over Omxplayer.

Play allows you to play audio and video files and organize them in playlists.
You can easily save these playlists (SQLite database) to continue them later on,
starting from the file where you leaved.
"""

import argparse
import datetime
import getpass
import glob
import mimetypes
import os
import random
try:
    import settings
except ImportError:
    settings = None
import sqlite3
import sys


__author__ = "Enric Caumons"
__email__ = "caumons@gmail.com"
__license__ = "GPLv3"


# Settings:
DB_PATH = getattr(settings, 'DB_PATH', os.path.join(os.path.dirname(os.path.realpath(__file__)), 'playlists.db'))
AUDIO_MOUNT_POINT = getattr(settings, 'AUDIO_MOUNT_POINT', '')
VIDEO_MOUNT_POINT = getattr(settings, 'VIDEO_MOUNT_POINT', '')
OMXPLAYER_WIN = getattr(settings, 'OMXPLAYER_WIN', '')  # Use omxplayer --win format
EXCLUDED_FORMATS = getattr(settings, 'EXCLUDED_FORMATS', ('.m3u',))


class Play:
    def __init__(self):
        self.playlist_dao = PlaylistDao()
        args = self.parse_args()
        self.bucle = args.bucle
        self.shuffle = args.shuffle
        self.limit = args.limit
        self.offset = args.offset
        self.output = args.output
        self.win = args.win
        self.playlist_name = args.playlist.lower() if args.playlist else None
        if args.type == 'both':
            self.type = ('audio', 'video')
        elif args.type == 'auto':
            self.type = None
        else:
            self.type = args.type
        self.playlists = args.playlists
        self.recursive = args.recursive
        self.update = args.update.lower() if args.update else None
        self.delete = args.delete.lower() if args.delete else None
        self.delete_all = args.delete_all
        self.paths = args.paths
        self.set_playlist()
        self.interpret_args()

    def parse_args(self):
        arg_parser = argparse.ArgumentParser(description="Playlist wrapper for OMXPlayer")
        arg_parser.add_argument('-b', '--bucle', action='store_true', help="Repeat playlist")
        arg_parser.add_argument('-s', '--shuffle', action='store_true', help="Random playlist")
        arg_parser.add_argument('-l', '--limit', type=int, default=0, help="Limit number of files")
        arg_parser.add_argument('-f', '--offset', type=int, default=0, help="Skip number of files")
        arg_parser.add_argument('-o', '--output', choices=['hdmi', 'local', 'both'], default='both',
                                help="Audio output device")
        arg_parser.add_argument('-w', '--win', help="Set position of video window")
        arg_parser.add_argument('-n', '--playlist', help="New playlist")
        arg_parser.add_argument('-t', '--type', choices=['audio', 'video', 'both', 'auto'], default='both',
                                help="Media type. If auto, type is guessed from first valid file")
        arg_parser.add_argument('-p', '--playlists', action='store_true', help="List user playlists")
        arg_parser.add_argument('-r', '--recursive', action='store_true',
                                help="Search files at subdirectories recursively")
        arg_parser.add_argument('-u', '--update', help="Update playlist from file system")
        arg_parser.add_argument('-d', '--delete', help="Delete user playlist")
        arg_parser.add_argument('-D', '--delete-all', action='store_true', help="Delete all user playlists")
        arg_parser.add_argument('paths', nargs='*', help="File paths or playlist")
        args = arg_parser.parse_args()
        return args

    def validate_file(self, path, playlist_type=None):
        allowed_types = playlist_type or self.type or ('audio', 'video')
        mime_type = mimetypes.guess_type(path)[0]
        return (not os.path.isdir(path) and mime_type and mime_type.startswith(allowed_types) and
                not path.endswith(EXCLUDED_FORMATS))

    def escape_path(self, path):
        return path.replace('[', '[[]').replace('*', '[*]').replace('?', '[?]')

    def colored(self, text):
        return '\033[93m%s\033[0m' % text

    def set_playlist(self):
        self.index = 0
        self.loaded = False
        playlist = []
        if len(self.paths) == 1:
            loaded_playlist = self.playlist_dao.get(self.paths[0].lower())
            if loaded_playlist:
                playlist = loaded_playlist['content'].split('\n')
                self.playlist_name = loaded_playlist['name']
                self.type = (tuple(loaded_playlist['type'].split('/'))
                             if '/' in loaded_playlist['type'] else loaded_playlist['type'])
                self.index = loaded_playlist['next']
                self.loaded = True
        if not playlist:
            for path in self.paths:
                path = path.strip()
                if path == '.':
                    path = os.getcwd()
                elif not path.startswith('/'):
                    path = os.path.join(os.getcwd(), path)
                if os.path.exists(path):
                    if os.path.isdir(path):
                        if self.recursive:
                            for root, dirnames, filenames in os.walk(path):
                                dirnames.sort(key=lambda p: p.lower())
                                for filename in sorted(filenames, key=lambda p: p.lower()):
                                    new_path = os.path.join(root, filename)
                                    if self.validate_file(new_path):
                                        playlist.append(new_path)
                        else:
                            playlist += [new_path for new_path
                                         in sorted(glob.glob(os.path.join(self.escape_path(path), '*')),
                                                   key=lambda p: p.lower())
                                         if self.validate_file(new_path)]
                    elif self.validate_file(path):
                        playlist.append(path)
                else:
                    playlist += [new_path for new_path in sorted(glob.glob(self.escape_path(path)))
                                 if self.validate_file(new_path)]
            if playlist and not self.type:
                first_file = playlist[0]
                self.type = mimetypes.guess_type(first_file)[0].split('/')[0]
                print("\nGuessed type is '%s' from first file '%s'" % (self.type, os.path.basename(first_file)))
                playlist = [filepath for filepath in playlist if self.validate_file(filepath)]
            if 0 < self.offset < len(playlist):
                playlist = playlist[self.offset:]
            if 0 < self.limit <= len(playlist):
                playlist = playlist[:self.limit]
        self.playlist = playlist
        self.playlist_len = len(playlist)
        if playlist:
            if self.shuffle:
                random.shuffle(playlist)
                if self.loaded:
                    self.playlist_dao.update(self.playlist_name, self.index, self.playlist)
            if self.playlist_name and not self.loaded:
                self.playlist_dao.save(self.playlist_name, self.type, self.playlist)
                print("Created new playlist '%s'" % self.playlist_name)

    def interpret_args(self):
        if self.playlists:
            playlists = self.playlist_dao.get()
            if playlists:
                print("Playlists:")
                for playlist in playlists:
                    playlist_files = playlist['content'].split('\n')
                    current_file = os.path.basename(playlist_files[playlist['next']])
                    print("- '%s' (%s) %d/%d >> '%s'" % (
                          playlist['name'], playlist['type'], playlist['next'] + 1, len(playlist_files), current_file))
            else:
                print("No playlists found")
            sys.exit()
        elif self.update:
            playlist = self.playlist_dao.get(self.update)
            if playlist:
                playlist_dirs = []
                for playlist_file in playlist['content'].split('\n'):
                    file_dir = os.path.join(os.path.dirname(os.path.realpath(playlist_file)), '*')
                    if file_dir not in playlist_dirs:
                        playlist_dirs.append(file_dir)
                playlist_type = tuple(playlist['type'].split('/')) if '/' in playlist['type'] else playlist['type']
                updated_files = []
                for playlist_dir in playlist_dirs:
                    updated_files += [new_path for new_path in sorted(glob.glob(playlist_dir))
                                      if self.validate_file(new_path, playlist_type)]
                self.playlist_dao.update(self.update, playlist['next'], updated_files)
                print("Updated playlist '%s'" % self.update)
            else:
                print("Playlist '%s' does not exist" % self.update)
            sys.exit()
        elif self.delete:
            if self.playlist_dao.get(self.delete):
                self.playlist_dao.delete(self.delete)
                print("Deleted playlist '%s'" % self.delete)
            else:
                print("Playlist '%s' does not exist" % self.delete)
            sys.exit()
        elif self.delete_all:
            playlists = self.playlist_dao.get()
            if playlists:
                print("Deleting playlists...")
                for playlist in playlists:
                    print("- '%s' (%s)" % (playlist['name'], playlist['type']))
                self.playlist_dao.delete()
                print("Done")
            else:
                print("No playlists found")
            sys.exit()
        elif self.playlist_len == 0:
            sys.exit("There are no files to play!")

        for media_type, mount_point in (('audio', AUDIO_MOUNT_POINT), ('video', VIDEO_MOUNT_POINT)):
            if mount_point and media_type in self.type and not os.path.ismount(mount_point):
                os.system('mount ' + mount_point)
                if not os.path.ismount(mount_point):
                    sys.exit(self.colored("'%s' could not be mounted, is it available?" % mount_point))

    def get_player_args(self, filename):
        player_args = '-o %s' % self.output
        if mimetypes.guess_type(filename)[0].startswith('video'):
            player_args += ' --aspect-mode stretch'
            if self.win:
                player_args += ' --win "%s"' % self.win
            elif OMXPLAYER_WIN:
                player_args += ' --win "%s"' % OMXPLAYER_WIN
        return player_args

    def print_playlist(self):
        print("\n%d Files at playlist:" % self.playlist_len)
        print('\n'.join(
              '%02d. %s' % (index, os.path.basename(filename)) for index, filename in enumerate(self.playlist, 1)))

    def get_next_index(self):
        if self.index < self.playlist_len - 1:
            self.index += 1
        else:
            if self.bucle:
                self.index = 0
                if self.shuffle:
                    random.shuffle(self.playlist)
                    if self.loaded:
                        self.playlist_dao.update(self.playlist_name, self.index, self.playlist)
                print("\nStarting again because bucle option is activated...")
                self.print_playlist()
            else:
                self.index = None
        return self.index

    def play_playlist(self):
        """
        Using os.system() to play files instead of subprocess.call() because we want to block signals
        while the player is running (e.g. SIGKILL). For more info read:
        http://stackoverflow.com/questions/27077509/how-is-python-blocking-signals-while-os-systemsleep
        """
        while self.index is not None:
            filename = self.playlist[self.index]
            if not os.path.exists(filename):
                sys.exit(self.colored("\n'%s' could not be played, is it available?" % filename))
            print("\n%02d. Playing '%s'..." % (self.index + 1, os.path.basename(filename)))
            if self.playlist_name:
                self.playlist_dao.update(self.playlist_name, self.index)
            command = 'omxplayer %s "%s"' % (self.get_player_args(filename), filename)
            play_exitcode = os.system(command)
            if play_exitcode == 2:  # ^c pressed
                self.print_playlist()
                input_val = input(("\nnext file? (current is %d: '%s') [n]/y/number\n" % (
                    self.index + 1, os.path.basename(filename)))).strip().lower()
                if input_val in ('', 'n'):
                    self.index = None
                elif input_val == 'y':
                    self.get_next_index()
                else:
                    try:
                        next = int(input_val) - 1
                    except ValueError:
                        pass  # Play same file again
                    else:
                        if 0 <= next < self.playlist_len:
                            self.index = next
                        else:
                            pass  # Play same file again
            else:
                self.get_next_index()

    def play(self):
        try:
            self.print_playlist()
            self.play_playlist()
        except KeyboardInterrupt:
            pass
        self.playlist_dao.close()
        print("\nBye! :)")


class PlaylistDao:
    def __init__(self):
        self.connection = sqlite3.connect(DB_PATH, isolation_level=None)  # Connect with autocommit
        self.connection.row_factory = sqlite3.Row
        self.cursor = self.connection.cursor()
        self.init_db()
        self.user = getpass.getuser()

    def init_db(self):
        with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'db.sql')) as db_sql:
            self.cursor.executescript(db_sql.read())

    def get(self, name=None):
        if name:
            args = (name, self.user)
            return self.cursor.execute("SELECT * FROM Playlist WHERE name = ? AND owner = ?", args).fetchone()
        else:
            args = (self.user,)
            return self.cursor.execute("SELECT * FROM Playlist WHERE owner = ? ORDER BY updated DESC", args).fetchall()

    def save(self, name, playlist_type, content, index=0):
        playlist_type_str = '/'.join(playlist_type) if type(playlist_type) == tuple else playlist_type
        args = (name, playlist_type_str, '\n'.join(content), index, self.user)
        try:
            self.cursor.execute("INSERT INTO Playlist (name, type, content, next, owner) VALUES (?, ?, ?, ?, ?)", args)
        except sqlite3.IntegrityError:
            print("Playlist '%s' already exists. Save skipped." % name)

    def update(self, name, index, content=None):
        updated = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        if content:
            args = ('\n'.join(content), index, updated, name, self.user)
            self.cursor.execute(
                "UPDATE Playlist SET content = ?, next = ?, updated = ? WHERE name = ? AND OWNER = ?", args)
        else:
            args = (index, updated, name, self.user)
            self.cursor.execute("UPDATE Playlist SET next = ?, updated = ? WHERE name = ? AND OWNER = ?", args)

    def delete(self, name=None):
        if name:
            args = (name, self.user)
            self.cursor.execute("DELETE FROM Playlist WHERE name = ? AND owner = ?", args)
        else:
            args = (self.user,)
            self.cursor.execute("DELETE FROM Playlist WHERE owner = ?", args)

    def close(self):
        return self.connection.close()


if __name__ == '__main__':
    Play().play()
