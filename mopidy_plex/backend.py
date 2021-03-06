# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from mopidy import backend, httpclient

import pykka
import requests


from plexapi.server import PlexServer
from plexapi.library import MusicSection
from plexapi.myplex import MyPlexAccount
from .playback import PlexPlaybackProvider
from .library import PlexLibraryProvider

import mopidy_plex
from mopidy_plex import logger

def get_requests_session(proxy_config, user_agent):
    proxy = httpclient.format_proxy(proxy_config)
    full_user_agent = httpclient.format_user_agent(user_agent)

    session = requests.Session()
    session.proxies.update({'http': proxy, 'https': proxy})
    session.headers.update({'user-agent': full_user_agent})

    return session


class PlexBackend(pykka.ThreadingActor, backend.Backend):
    def __init__(self, config, audio):
        super(PlexBackend, self).__init__(audio=audio)
        self.config = config
        self.session = get_requests_session(proxy_config=config['proxy'],
                                            user_agent='%s/%s' % (mopidy_plex.Extension.dist_name,
                                                                  mopidy_plex.__version__)
                                           )
        baseurl = (config['plex']['server'])
        token = (config['plex']['token'])
        self.plex = PlexServer(baseurl, token)
        self.music = [s for s in self.plex.library.sections() if s.TYPE == MusicSection.TYPE][0]
        logger.debug('Found music section on plex server %s: %s', self.plex, self.music)
        self.library_id = config['plex']['library_id']
        self.uri_schemes = ['plex', ]
        self.library = PlexLibraryProvider(backend=self)
        self.playback = PlexPlaybackProvider(audio=audio, backend=self)



    def plex_uri(self, uri_path, prefix='plex'):
        '''Get a leaf uri and complete it to a mopidy plex uri.

        E.g. plex:artist:3434
             plex:track:2323
             plex:album:2323
             plex:playlist:3432
        '''
        uri_path = str(uri_path)
        if not uri_path.startswith('/library/metadata/'):
            uri_path = '/library/metadata/' + uri_path

        if uri_path.startswith('/library/metadata/'):
            uri_path = uri_path[len('/library/metadata/'):]
        return '{}:{}'.format(prefix, uri_path)

    def resolve_uri(self, uri_path):
        '''Get a leaf uri and return full address to plex server'''
        uri_path = str(uri_path)
        if not uri_path.startswith('/library/metadata/'):
            uri_path = '/library/metadata/' + uri_path
        return self.plex.url(uri_path)
