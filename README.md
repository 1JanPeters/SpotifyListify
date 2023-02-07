# SpotifyListify

## About SpotifyListify

This program uses the Spotify api to find all the songs in your library, including albums, favorites
and other playlists and put them all in one playlist. Due to limitations from Spotify 
the lists might have a size limit. Because of that another list are created and filled if the previous one is full.

Motivation is that you might want to load all your songs on your phone. Because the current 
workflow does not allow to download all songs in your library easily it is very time-consuming.
With few lists that contain every song you have in your library you can hit just a few 
download buttons to queue all your songs to download.

Another motivation is to have a list off all your songs since this basic feature is not
supported by Spotify.

## Usage

- Create an app at https://developer.spotify.com
- Copy & paste the config.ini.example and remove the '.example'
- Next you have to replace the credentials from the ones from the spotify dashboard
  - client_id: Client ID in the app dashboard
  - client_secret: Also in the app dashboard
  - userid: The userid can be retrieved from the link to the user account - For the desktop app
  you can right-click and copy the link, then you should have a link like: 
  https://open.spotify.com/user/userid?si=...&nd=1 for browser its just https://open.spotify.com/user/userid
- You can leave the SPOTIPY_REDIRECT_URI as it is if you want to run SpotifyListify locally.

Please note that the use of the project is at your own risk, because even if the developer community had no problems using it, we cannot guarantee that there will be no unforeseeable errors in its execution!
