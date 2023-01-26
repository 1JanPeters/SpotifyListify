import configparser
import time

import spotipy
from spotipy import SpotifyException
from spotipy.oauth2 import SpotifyOAuth

scope = 'playlist-read-private user-library-read playlist-modify-private'

list_number = 1
playlistName = "All Songs"
counter = 0
created_lists = []
all_playlist = None
userid = None


def choose_playlist():
    playlists = sp.current_user_playlists()
    name = None
    while playlists:
        for i, playlist in enumerate(playlists['items']):
            print("%4d %s %s" % (i + playlists['offset'], playlist['uri'], playlist['name']))
        playlist_choice = input("n for next, else number of playlist")
        if playlist_choice.isdecimal():
            if (len(playlists['items'])+playlists['offset']) > int(playlist_choice) > -1+playlists['offset']:
                name = playlists['items'][int(playlist_choice)-playlists['offset']]['name']
                playlists = None
        if playlists is not None and playlists['next']:
            playlists = sp.next(playlists)
        else:
            playlists = None
    return name


def find_playlist_by_name(name):
    playlists = sp.current_user_playlists()
    while playlists:
        for i, playlist in enumerate(playlists['items']):
            if playlist['name'] == name:
                return playlist
        if playlists is not None and playlists['next']:
            playlists = sp.next(playlists)
        else:
            exit("Failure at creating finding playlist " + name)
    exit("Failure at creating finding playlist " + name)


def split_uris_into_chunks(uris, limit=100):
    return [uris[i:i + limit] for i in range(0, len(uris), limit)]


def handle_spotifyexception(ex, is_error):
    global all_playlist, userid, list_number, created_lists
    template = "An exception of type {0} occurred. Arguments:\n{1!r}"
    message = template.format(type(ex).__name__, ex.args)
    print(message)
    if str(ex.args).__contains__("Playlist size limit reached"):
        if is_error:
            exit("Unexpected Infinite Loop Error")
        list_number += 1
        new_playlist_name = playlistName + " " + str(list_number)
        sp.user_playlist_create(name=new_playlist_name, public=False, user=userid)
        time.sleep(5)
        all_playlist = find_playlist_by_name(new_playlist_name)
        created_lists.append(all_playlist['id'])
        is_error = True
    else:
        exit("Unexpected SpotifyException")
    return is_error


# Adds the tracks from the uri list to the list, if the list is full a new list gets created and returned
def add_tracks_to_list(uris):
    global list_number, counter, all_playlist
    uris = remove_local_uris(uris)
    uris_chunks = split_uris_into_chunks(uris, limit=100)
    for uris_chunk in uris_chunks:
        is_error = False
        while True:
            try:
                sp.playlist_add_items(playlist_id=all_playlist['id'], items=uris_chunk)
                break
            except SpotifyException as ex:
                handle_spotifyexception(ex, is_error)
    counter += len(uris)


def remove_local_uris(uris):
    cleaned_uris = []
    for uri in uris:
        if not uri.__contains__('spotify:local'):
            cleaned_uris.append(uri)
    return cleaned_uris


def add_songs():
    global all_playlist
    saved_tracks = sp.current_user_saved_tracks(limit=20)
    while saved_tracks:
        uris: list = []
        for track in saved_tracks['items']:
            uris.append(track["track"]["uri"])
        add_tracks_to_list(uris)
        if saved_tracks is not None and saved_tracks['next']:
            saved_tracks = sp.next(saved_tracks)
        else:
            saved_tracks = None


def playlist_is_created_playlist(playlist_id):
    for id in created_lists:
        if id == playlist_id:
            return True
    return False


def get_album_tracks(playlist, uris):
    tracks = sp.playlist_tracks(playlist['id'])
    while tracks:
        for track in tracks['items']:
            uris.append(track['track']['uri'])
        if tracks is not None and tracks['next']:
            tracks = sp.next(tracks)
        else:
            tracks = None


def is_playlist_to_add(playlist, own_lists=True, subscribed_lists=True):
    current_user_id = sp.current_user()['id']
    if (own_lists and playlist['owner']['id'] != current_user_id) and not subscribed_lists:
        return False
    if (subscribed_lists and playlist['owner']['id'] == current_user_id) and not own_lists:
        return False
    if playlist_is_created_playlist(playlist_id=playlist['id']):
        return False
    return True


def add_playlists(own_lists=True, subscribed_lists=True):
    global all_playlist
    if not own_lists and not subscribed_lists:
        return
    saved_playlists = sp.current_user_playlists(limit=30)
    while saved_playlists:
        uris: list = []
        for i, playlist in enumerate(saved_playlists['items']):
            if not is_playlist_to_add(playlist, own_lists=own_lists, subscribed_lists=subscribed_lists):
                continue
            get_album_tracks(playlist, uris)
            print(i + 1, playlist['id'], playlist['uri'], playlist['name'])
            add_tracks_to_list(uris)
        if saved_playlists['next']:
            saved_playlists = sp.next(saved_playlists)
        else:
            saved_playlists = None


def get_album_tracks(album, uris):
    tracks = sp.album_tracks(album['album']['id'])
    while tracks:
        for track in tracks['items']:
            uris.append(track["uri"])
        if tracks is not None and tracks['next']:
            tracks = sp.next(tracks)
        else:
            tracks = None


def add_albums():
    global all_playlist
    saved_albums = sp.current_user_saved_albums(limit=50)
    while saved_albums:
        uris: list = []
        for i, album in enumerate(saved_albums['items']):
            get_album_tracks(album, uris=uris)
            print(i + 1, album['album']['id'], album['album']['uri'], album['album']['name'])
        add_tracks_to_list(uris)
        if saved_albums['next']:
            saved_albums = sp.next(saved_albums)
        else:
            saved_albums = None


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

    print("Welcome to SpotifyListify, a tool to fetch all the songs in your library and put them in one list")
    print("By doing so you can for example download the list on your phone without having to download every artist "
          "after another")
    print("Enter:\n"
          "1 To select a playlist from your account\n"
          "2 to create a new name")
    choice = ""
    while (not choice.isdecimal()) or (choice != "1" and choice != "2"):
        choice = input(">")
    if choice == "1":
        playlistName = choose_playlist()
    if choice == "2":
        playlistName = input("New playlist name:>")
        sp.user_playlist_create(name=playlistName, public=False, user=userid)

    all_playlist = find_playlist_by_name(playlistName)
    created_lists.append(all_playlist['id'])
    if all_playlist is None:
        exit("Could not create/find a playlist")
    #add_playlists()
    add_songs()
    add_albums()

    print("Number of songs ", counter)
