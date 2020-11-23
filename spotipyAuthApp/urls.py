from django.urls import path
from . import views

urlpatterns = [
    # Login
    path('', views.login, name =  'Login'),
    path('login/', views.spot_login),
    path('loginuser/', views.login_user, name = 'LoginUser'),
    path('notyou/', views.not_you, name = 'NotYou'),
    path('register/', views.register, name = 'Register'),
    ##Home Page
    path('home/', views.start, name = 'Start'),
    path('addtape/', views.add_tape, name = 'AddTape'),
    path('deletetape/<int:id>/', views.delete_tape, name = 'DeleteTape'),
    ##Tape Info Page
    path('tapeinfo/<int:id>/', views.tape_info, name= 'TapeInfo'),
    path('searchsong/', views.search_song, name = 'SearchSong'),
    path('sharetape/', views.share_tape, name = 'ShareTape'),
    path('burntape/', views.burn_tape, name = 'BurnTape'),
    path('addsong/', views.add_song, name = "AddSong"),
    path('removesong/', views.remove_song, name= "RemoveSong"),
    path('shuffle/', views.shuffle, name = 'Shuffle'),
    path('playsong/', views.play_song, name = 'PlaySong'),
    path('pausesong/', views.pause_song, name = 'PauseSong'),
    ##Edit Tape
    path('toeditburn/<int:id>/', views.to_edit_burn, name = 'ToEditBurn'),
    ##Explore Page
    path('explore/', views.explore, name = 'Explore'),
    # path('rerouteinfo/<int:id>/', views.reroute_info, name = 'RerouteInfo'),
    # path('callback/', views.reroute_home, name = "RerouteHome"), 
    ##Logout paths
    path('logout/', views.logout, name = 'Logout'),
    path('reroutelogin', views.reroute_login, name = 'RerouteLogin'),
]