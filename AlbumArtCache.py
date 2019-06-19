from mutagen import File
import time
import os
from mpd import MPDClient


def read_album_art(music_file, out_file):
    mutagen_file = File(music_file)

    keys = mutagen_file.tags.keys()
    if 'APIC:' in keys:
        artwork = mutagen_file.tags['APIC:'].data

    elif 'APIC:Cover' in keys:
        artwork = mutagen_file.tags['APIC:Cover'].data

    elif 'APIC:"Album cover"' in keys:
        artwork = mutagen_file.tags['APIC:"Album cover"'].data
    else:
        raise KeyError("no album art found")

    with open(out_file, 'wb') as img:
        img.write(artwork)


class AlbumArtCache:

    def __init__(self, cache_path, music_path, default_album_art):

        self.__default_album_art = default_album_art
        self.__cache_path = cache_path
        self.__music_path = music_path
        self.__album_arts = {os.path.splitext(album_art)[0]: cache_path + '/' + album_art for album_art in
                             os.listdir(cache_path)}

    def get_album_art(self, song):

        if 'album' not in song:
            if 'title' in song:
                song['album'] = song['title']
            else:
                return self.__default_album_art

        if 'artist' not in song:
            song['artist'] = 'unknown'

        album_art_name = song['artist'] + '-' + song['album']
        if album_art_name in self.__album_arts:
            return self.__album_arts[album_art_name]
        else:
            return self.cache_album_art(song)

    def get_album_art_album(self, mpd_client, album):
        song_list = mpd_client.find('album', album)
        if song_list:
            return self.get_album_art(song_list[0])
        else:
            return self.__default_album_art

    def get_album_art_artist(self, mpd_client, artist):
        if artist in self.__album_arts:
            return self.__album_arts[artist]
        else:
            return self.cache_album_art_artist(mpd_client, artist)

    def get_album_art_folder(self, mpd_client, folder):
        cached_name = folder.replace('/', '_')
        if cached_name in self.__album_arts:
            return self.__album_arts[cached_name]
        else:
            return self.cache_album_art_folder(mpd_client, folder)

    def get_album_art_playlist(self, mpd_client, playlist):
        cached_name = '_' + playlist
        if cached_name in self.__album_arts:
            return self.__album_arts[cached_name]
        else:
            return self.cache_album_art_playlist(mpd_client, playlist)

    def cache_album_art(self, song):

        album_art_name = song['artist'] + '-' + song['album']
        album_art_file = self.__cache_path + '/' + album_art_name

        try:
            read_album_art(self.__music_path + '/' + song['file'], album_art_file)

        except KeyError:
            print "no album art found for " + song['album']
            album_art_file = self.__default_album_art

        self.__album_arts[album_art_name] = album_art_file
        return album_art_file

    def find_and_cache_album_art(self, song_list, cached_name):
        if song_list:
            for song in song_list:
                album_art = self.get_album_art(song)
                if album_art is not self.__default_album_art:
                    self.__album_arts[cached_name] = album_art
                    return album_art
        self.__album_arts[cached_name] = self.__default_album_art
        return self.__default_album_art

    def cache_album_art_artist(self, mpd_client, artist):

        song_list = mpd_client.find('artist', artist)
        return self.find_and_cache_album_art(song_list, artist)

    def cache_album_art_folder(self, mpd_client, folder):
        cached_name = folder.replace('/', '_')

        # no song matches only a directory -> search instead of find
        song_list = mpd_client.search('file', folder)
        # remove matches in the middle
        song_list = list(filter(lambda path: path['file'].startswith(folder), song_list))

        return self.find_and_cache_album_art(song_list, cached_name)

    def cache_album_art_playlist(self, mpd_client, playlist):
        cached_name = '_' + playlist

        song_list = mpd_client.listplaylistinfo(playlist)

        return self.find_and_cache_album_art(song_list, cached_name)


def init_default_cache(music_path):
    if 'XDG_CACHE_HOME' in os.environ:
        cache_path = os.environ['XDG_CACHE_HOME'] + "/mpd-album-art"
    else:
        print("setting cache dir to default location\n")
        cache_path = os.environ['HOME'] + "/.cache/mpd-album-art"
    print("cache dir: " + cache_path)

    if not os.path.isdir(cache_path):
        os.makedirs(cache_path)

    return AlbumArtCache(cache_path, music_path, "images/icon.png")


def test(song):
    cache = init_default_cache("/home/felix/data/music")

    start = time.time()
    print (cache.get_album_art(song))
    end = time.time()
    print end - start
