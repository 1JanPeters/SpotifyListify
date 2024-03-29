import configparser
import time

import spotipy
from spotipy import SpotifyException
from spotipy.oauth2 import SpotifyOAuth

scope = 'playlist-read-private user-library-read playlist-modify-private'

list_number = 1
playlistName = "All Songs"
playlistUri = None
counter = 0
created_lists = []
all_playlist = None
userid = None

uris_added: dict = {}

spacer = "▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮"


def select_a_playlist(playlists, user_input):
    if (len(playlists['items']) + playlists['offset']) > int(user_input) > -1 + playlists['offset']:
        return playlists['items'][int(user_input) - playlists['offset']]['uri']


def get_next_playlists_page(playlists):
    if playlists['offset'] % len(playlists['items']) == 0:
        if playlists is not None and playlists['next']:
            return sp.next(playlists)
        else:
            return None
    else:
        print('You reached the end')
        return playlists


def choose_playlist():
    playlists = sp.current_user_playlists()
    while playlists:
        for i, playlist in enumerate(playlists['items']):
            print("%4d %s %s" % (i + playlists['offset'], playlist['uri'], playlist['name']))
        user_input = input("Enter number of playlist, n for next page, m for menu\n➤")
        if user_input.isdecimal():
            return select_a_playlist(playlists, user_input)
        if user_input == 'n':
            playlists = get_next_playlists_page(playlists)
        if user_input == 'm':
            return False


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
    uris = remove_already_added_uris(uris)
    uris_chunks = split_uris_into_chunks(uris, limit=100)
    for uris_chunk in uris_chunks:
        is_error = False
        while True:
            try:
                sp.playlist_add_items(playlist_id=all_playlist['id'], items=uris_chunk)
                break
            except SpotifyException as ex:
                handle_spotifyexception(ex, is_error)
    remember_the_added_uris(uris)
    counter += len(uris)


def remove_local_uris(uris):
    cleaned_uris = []
    for uri in uris:
        if not uri.__contains__('spotify:local'):
            cleaned_uris.append(uri)
    return cleaned_uris


def remove_already_added_uris(uris):
    cleaned_uris = []
    for uri in uris:
        if uri not in uris_added:
            cleaned_uris.append(uri)
    return cleaned_uris


def remember_the_added_uris(uris):
    for uri in uris:
        uris_added[uri] = 1


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
    for created_lists_id in created_lists:
        if created_lists_id == playlist_id:
            return True
    return False


def get_playlist_tracks(playlist, uris):
    tracks = sp.playlist_items(playlist['id'], additional_types=('track',))
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
            get_playlist_tracks(playlist, uris)
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
    choice = ""
    while (not choice.isdecimal()) or (choice != "1" and choice != "2"):
        print(spacer)
        print("Welcome to SpotifyListify, a tool to fetch all the songs in your library and put them in one list")
        print("By doing so you can for example download the list on your phone without having to download every artist "
              "after another")
        print("Enter:\n"
              "1 To select a playlist from your account\n"
              "2 to create a new name\n")
        choice = input("➤")
        if choice == "1":
            playlistUri = choose_playlist()
            if playlistName is False:
                choice = '-1'
            all_playlist = sp.playlist(playlist_id=playlistUri)
        if choice == "2":
            playlistName = input("➤New playlist name: ")
            sp.user_playlist_create(name=playlistName, public=False, user=userid)
            all_playlist = find_playlist_by_name(playlistName)

    created_lists.append(all_playlist['id'])
    if all_playlist is None:
        exit("Could not create/find a playlist")

    choice = ''
    is_addsongs = False
    is_addalbums = False
    is_addplaylists = False
    is_own_lists = False
    is_sub_lists = False
    while choice != "y":
        print(spacer)
        print('Current settings: Add Songs: %s, Add Albums: %s, Add Playlists: %s' % (is_addsongs, is_addalbums,
                                                                                      is_addplaylists))
        print("Enter:\n"
              "1 To toggle favorite songs\n"
              "2 To toggle liked albums\n"
              "3 To toggle playlists\n"
              "y to confirm or e to exit")
        choice = input("➤")
        if choice == '1':
            is_addsongs = not is_addsongs
        elif choice == '2':
            is_addalbums = not is_addalbums
        elif choice == '3':
            is_addplaylists = not is_addplaylists
        elif choice == 'e':
            exit(0)

    if is_addplaylists:
        choice = ''
        while choice != "y":
            print(spacer)
            print('Current settings: Own Playlists: %s, Subscribed Playlists: %s' % (is_own_lists, is_sub_lists))
            print("Enter:\n"
                  "1 To toggle Own Playlists\n"
                  "2 To toggle Subscribed Playlists\n"
                  "y to confirm or e to exit")
            choice = input("➤")
            if choice == '1':
                is_own_lists = not is_own_lists
            elif choice == '2':
                is_sub_lists = not is_sub_lists
            elif choice == 'e':
                exit(0)
    if is_addsongs:
        add_songs()
    if is_addalbums:
        add_albums()
    if is_addplaylists:
        add_playlists(own_lists=is_own_lists, subscribed_lists=is_sub_lists)
    print("Number of songs ", counter)
