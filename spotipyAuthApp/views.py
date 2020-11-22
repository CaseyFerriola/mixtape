from django.shortcuts import render, redirect, HttpResponse
import spotipy, bcrypt, sys, os, random, string
import spotipy.util as util
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth
from .env import client_id, client_secret
from ast import literal_eval
from django.contrib import messages
from .models import User, MixTape
from json.decoder import JSONDecodeError

scope = "user-library-read user-follow-read playlist-read-private playlist-modify-private playlist-modify-public streaming user-read-playback-state"
# if 'cache_id' not in request.session
# client_credentials_manager = SpotifyClientCredentials(client_id= client_id, client_secret= client_secret)
def delete_request(request):
    del request.session['cache_id']
    return
# username = 'ferriolac1'
def get_random_alphanumeric_string(length):
    letters_and_digits = string.ascii_letters + string.digits
    result_str = ''.join((random.choice(letters_and_digits) for i in range(length)))
    return result_str

def not_you(request):
    os.remove(get_cache_path(request.session['cache_id']))
    delete_request(request)
    if 'curr_user' in request.session:
        del request.session['curr_user']
    return redirect('/')

def login(request):
    # delete_request(request)
    
    if 'cache_id' in request.session:
        context = {
            'spot_status': True,
            'user': get_spotify_object(request).current_user()
        }
        request.session['curr_user_sid'] = get_spotify_object(request).current_user()['id']
    else:
        context = {
            'spot_status': False
        }
        
    return render(request, 'login.html', context)
    
def login_user(request):
    errors = User.objects.login_validator(request, request.POST)
    if len(errors) > 0:
        for key, val in errors.items():
            messages.error(request, val, extra_tags= 'Login')
        return redirect('/')
    else:
        user = User.objects.get(email = request.POST['email'])
        request.session['curr_user'] = user.id
    return redirect('Start')

    
def get_cache_path(id):
    return '.\\spotipyAuthApp\\cache\\'+id


def get_spotify_object(request):
    auth_manager = SpotifyOAuth(cache_path= get_cache_path(request.session['cache_id']))
    return spotipy.Spotify(auth_manager= auth_manager)


def spot_login(request):
    if 'cache_id' not in request.session:
        #create random cache
        request.session['cache_id'] = get_random_alphanumeric_string(14)


    auth_manager = SpotifyOAuth(client_id = client_id, client_secret = client_secret, redirect_uri= 'http://localhost:8000/login/', scope=scope, cache_path= get_cache_path(request.session['cache_id']), show_dialog= True)
    if 'code' in request.GET:
        print('Getting code')
        token = auth_manager.get_access_token(request.GET.get('code'))
        # print(token)
        return redirect('/')
    print(f'token: {auth_manager.get_cached_token()}')
    if not auth_manager.get_cached_token():
        print('Checking for Cache')
        url = auth_manager.get_authorize_url()
        return redirect(url)
    spotify_object = spotipy.Spotify(auth_manager=auth_manager)
    print('redirecting to login')
        # return HttpResponse(f'<h2><a href="{url}">Sign in</a></h2>')
    # spot = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(client_id= client_id, client_secret=client_secret))
    return redirect('Login')

def register(request):
    errors = User.objects.basic_validator(request.POST)
    if len(errors) > 0:
        for key, val in errors.items():
            messages.error(request, val, extra_tags= 'Register')
        return redirect('/')
    else:
        password = request.POST['password']
        print(get_spotify_object(request).current_user())
        curr_user_sid = get_spotify_object(request).current_user()['id']       
        pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        user = User.objects.create(email = request.POST['email'], aka = request.POST['aka'], spotify_id = curr_user_sid, password = pw_hash)
        request.session['curr_user'] = user.id
        
    return redirect('Start')

def reroute_home(request):
    return redirect('Start')

def find_playlists_not_loaded(curr_user_playlists):
    playlists = []
    for idx, item in enumerate(curr_user_playlists['items']):
        if len(MixTape.objects.filter(name= item['name'])) > 0:
            continue
        playlist_id = item['id']
        playlists.append({"name":item["name"], "id": {"id": playlist_id, "idx": idx}})
    return playlists
    
def start(request):
    if 'curr_user' not in request.session:
        return redirect('/')
    user = User.objects.get(id = request.session['curr_user'])
    curr_user_playlists = get_spotify_object(request).current_user_playlists(limit=50)
    playlists = find_playlists_not_loaded(curr_user_playlists)
    shared_tapes = user.mixtapes_shared.all()
    context = {
        'playlists': playlists,
        'tapes': user.mixtape.all(),
        'curr_user': user,
        'shared_tapes': shared_tapes
    }
    return render(request, 'home.html', context)





def add_tape(request):
    sp = get_spotify_object(request)
    user = User.objects.get(id = request.session['curr_user'])
    curr_user_playlists = sp.current_user_playlists(limit=50)
    ## making playlist id readable
    temp = request.POST['mixtape']
    mixtape_ids = literal_eval(temp)
    # print(mixtape_ids[0]['idx'])
    album_cover = curr_user_playlists['items'][int(mixtape_ids['idx'])]['images'][0]['url']
    desc = curr_user_playlists['items'][int(mixtape_ids['idx'])]['description']
    name = curr_user_playlists['items'][int(mixtape_ids['idx'])]['name']
    MixTape.objects.create(name = name, images = album_cover, created_by = user, spotify_id = mixtape_ids['id'], desc = desc)
    playlists = find_playlists_not_loaded(curr_user_playlists)
    context = {
        'playlists': playlists,
        'tapes': user.mixtape.all(),
        'curr_user': user
    }
    return render(request, 'addTape.html', context)

def tape_info(request, id):
    tape = MixTape.objects.get(id = id)
    mixtape = get_spotify_object(request).playlist_tracks(playlist_id= tape.spotify_id)
    users = User.objects.exclude(id = request.session['curr_user'])
    s = []
    count = 0
    for it in mixtape['items']:
        count += 1
        sArtists = [artist['name'] for artist in it['track']['artists']]
        s.append({'name': it['track']['name'], 'artists': sArtists,'id': it['track']['id'], 'num': count, 'uri': it['track']['uri']})
    context = {
        'users': users,
        'tape': tape,
        'songs': s
    }
    return render(request, 'mixtapeInfo.html', context)
def search_song(request):
    post = request.POST['new_song']
    results = get_spotify_object(request).search(q= post, limit= 15)
    tracks = results['tracks']
    searches = []
    count = 0
    for track in tracks['items']:
        count += 1
        searches.append({'name': track['name'], 'artist': track['artists'][0]['name'], 'id': track['id'], 'num': count})
    context = {
        'searches': searches,
        'tape_id': request.POST['tape_id']
    }
    return render(request, 'searchTable.html', context)
def share_tape(request):
    tape = MixTape.objects.get(id = request.POST['tape_id'])
    # mixtape = get_spotify_object(request).playlist_tracks(playlist_id= tape.spotify_id)
    # users = User.objects.exclude(id = request.session['curr_user'])
    # s = []
    # count = 0
    # for it in mixtape['items']:
    #     count += 1
    #     sArtists = [artist['name'] for artist in it['track']['artists']]
    #     s.append({'name': it['track']['name'], 'artists': sArtists,'id': it['track']['id'], 'num': count, 'uri': it['track']['uri']})
    if request.POST['share_with'] != 'all':
        share_with = User.objects.get(id= request.POST['share_with'])
        share_with.mixtapes_shared.add(tape)
    # context = {
    #     'users': users,
    #     'tape': tape,
    #     'songs': s
    # }
    return HttpResponse('The MixTape was shared with ' + share_with.aka)
def to_edit_burn(request, id):
    tape = MixTape.objects.get(id = id)
    context = {
        'tape': tape
    }
    return render(request, 'editBurn.html', context)
def remove_from_share(request, tape_id):
    user = User.objects.get(id = request.session['curr_user'])
    check = user.mixtapes_shared.filter(id = tape_id)
    if len(check) > 0:
        tape = MixTape.objects.get(id = tape_id)
        user.mixtapes_shared.remove(tape)
        user.save()
        return
    return


def burn_tape(request):
    sp = get_spotify_object(request)
    tape_to_burn = MixTape.objects.get(id = request.POST['tape_id'])
    remove_from_share(request, tape_to_burn.id)
    tape_id = tape_to_burn.spotify_id
    curr_tape = sp.playlist(tape_id)
    ##Check to see if user already has the playlist
    playlists = sp.current_user_playlists()
    for playlist in playlists['items']:
        if tape_id == playlist['id']:
            return HttpResponse('You already have this playlist')
    if request.POST['status'] == 'public':
        public = True
    else:
        public = False
    new_tape = sp.user_playlist_create(user = request.session['curr_user_sid'], name = request.POST['name'], public = public, description = request.POST['desc'])
    s = []
    for it in curr_tape['tracks']['items']:
        s.append(it['track']['id'])
    sp.playlist_add_items(new_tape['id'], s)
    return HttpResponse('The tape is successfully burned')
# def reroute_info(request, id):
#     return redirect('TapeInfo', id)
def list_of_track_objects(track_list):
    s = []
    count = 0
    for it in track_list['items']:
        count += 1
        sArtists = [artist['name'] for artist in it['track']['artists']]
        s.append({'name': it['track']['name'], 'artists': sArtists,'id': it['track']['id'], 'num': count })
    return s
def add_song(request):
    id = [request.POST['id']]
    tape_id = request.POST['tape_id']
    sp =  get_spotify_object(request)
    sp.playlist_add_items(tape_id, id)
    mixtape = sp.playlist_tracks(playlist_id= tape_id)
    s = list_of_track_objects(mixtape)
    context = {
        'songs': s,
        'tape_id': tape_id
    }
    return render(request, 'mixtapeSongsTable.html', context)
def remove_song(request):
    sp =  get_spotify_object(request)
    id = [request.POST['id']]
    tape_id = request.POST['tape_id']
    sp.playlist_remove_all_occurrences_of_items(playlist_id = tape_id, items = id)
    mixtape = sp.playlist_tracks(playlist_id= tape_id)
    s = list_of_track_objects(mixtape)
    context = {
        'songs': s,
        'tape_id': tape_id
    }
    return render(request, 'mixtapeSongsTable.html', context)

def play_song(request):
    print('hello')
    sp =  get_spotify_object(request)
    tape_id = request.POST['tape_id']
    # mixtape = sp.playlist_tracks(playlist_id= tape_id)
    # s = list_of_track_objects(mixtape)
    song_uri = request.POST['uri']
    song = sp.track(song_uri)
    # print(song)
    device = sp.devices()
    print('*'*80)
    print(device)
    sp.start_playback(uris = [song_uri], device_id = device['devices'][0]['id'])
    context = {
        'song': song,
        'tape_id': tape_id
    }
    return render(request, 'pause.html', context)
def pause_song(request):
    sp =  get_spotify_object(request)
    tape_id = request.POST['tape_id']
    mixtape = sp.playlist_tracks(playlist_id= tape_id)
    s = list_of_track_objects(mixtape)
    sp.pause_playback()
    context = {
        'songs': s,
        'tape_id': tape_id,
    }
    # return render(request, 'mixtapeSongsTable.html', context)
    return render(request, 'play.html', context)
def delete_tape(request, id):
    tape = MixTape.objects.get(id = id)
    tape.delete()
    return redirect('Start')

def logout(request):
    os.remove(get_cache_path(request.session['cache_id']))
    del request.session['cache_id']
    del request.session['curr_user']
    return redirect('RerouteLogin')

def reroute_login(request):
    return redirect('/')