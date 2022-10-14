import configparser
import time

import spotipy
from spotipy import SpotifyException
from spotipy.oauth2 import SpotifyOAuth

scope = 'playlist-read-private user-library-read playlist-modify-private'


def choose_playlist():
    playlists = sp.current_user_playlists()
    name = None
    while playlists:
        for i, playlist in enumerate(playlists['items']):
            print("%4d %s %s" % (i + playlists['offset'], playlist['uri'], playlist['name']))
        playlist_choice = input("n for next, else number of playlist")
        if playlist_choice.isdecimal():
            if len(playlists) > int(playlist_choice) > -1:
                name = playlists['items'][int(playlist_choice)]['name']
                playlists = None
        if playlists is not None and playlists['next']:
            playlists = sp.next(playlists)
        else:
            playlists = None
    return name


def find_playlist_by_name(name):
    playlists = sp.current_user_playlists()
    search_playlist = None
    while playlists:
        for i, playlist in enumerate(playlists['items']):
            # print("%4d %s %s" % (i + playlists['offset'], playlist['uri'], playlist['name']))
            if playlist['name'] == name:
                search_playlist = playlist
        if playlists is not None and playlists['next']:
            playlists = sp.next(playlists)
        else:
            playlists = None
    return search_playlist


if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read("config.ini")
    print(config.sections())
    credentials = config['credentials']
    network = config['network']
    userid = credentials['userid']
    client_id = credentials['client_id']
    client_secret = credentials['client_secret']
    SPOTIPY_REDIRECT_URI = network['SPOTIPY_REDIRECT_URI']

    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope, client_id=client_id,
                                                   client_secret=client_secret,
                                                   redirect_uri=SPOTIPY_REDIRECT_URI))
    saved_albums = sp.current_user_saved_albums()
    saved_tracks = sp.current_user_saved_tracks()
    index = 0
    counter = 0

    list_number = 1
    print("Welcome to SpotifyListify, a tool to fetch all the songs in your library and put them in one list")
    print("By doing so you can for example download the list on your phone without having to download every artist "
          "after another")
    print("Enter:\n"
          "1 To select a playlist from your account\n"
          "2 to create a new name")
    choice = ""
    while not choice.isdecimal():
        choice = input(">")
    if choice == "1":
        playlistName = choose_playlist()
    if choice == "2":
        playlistName = input("New playlist name:>")
        sp.user_playlist_create(name=playlistName, public=False, user=userid)

    all_playlist = find_playlist_by_name(playlistName)
    if all_playlist is None:
        exit("Could not create/find a playlist")
    while saved_albums:
        uris: list = []
        for i, album in enumerate(saved_albums['items']):
            tracks = sp.album_tracks(album['album']['id'])
            while (tracks):
                for track in tracks['items']:
                    uris.append(track["uri"])
                if tracks is not None and tracks['next']:
                    tracks = sp.next(tracks)
                else:
                    tracks = None
            print(i + 1, album['album']['id'], album['album']['uri'], album['album']['name'])
            counter += len(uris)
            try:
                sp.playlist_add_items(playlist_id=all_playlist['id'], items=uris)
                uris.clear()
            except SpotifyException as ex:
                template = "An exception of type {0} occurred. Arguments:\n{1!r}"
                message = template.format(type(ex).__name__, ex.args)
                print(message)
                if str(ex.args).__contains__("Playlist size limit reached"):
                    list_number += 1
                    newPlaylistName = playlistName + " " + str(list_number)
                    sp.user_playlist_create(name=newPlaylistName, public=False, user=userid)
                    time.sleep(10)
                    all_playlist = find_playlist_by_name(newPlaylistName)
                    if all_playlist is None:
                        exit("Failure at creating finding new playlist")
                else:
                    exit("Unexpected exception")
        if saved_albums['next']:
            saved_albums = sp.next(saved_albums)
        else:
            saved_albums = None
    print("Number of songs ", counter)
