# -*- coding: utf8 -*-
# This file is part of PyBossa.
#
# Copyright (C) 2015 SF Isle of Man Limited
#
# PyBossa is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PyBossa is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with PyBossa.  If not, see <http://www.gnu.org/licenses/>.

from mock import patch, MagicMock
from flask import Response, session
from default import flask_app
from pybossa.util import Flickr

class TestFlickrOauth(object):


    @patch('pybossa.view.flickr.flickr')
    def test_flickr_login_specifies_callback(self, flickr_oauth):
        flickr_oauth.oauth.authorize.return_value = Response(302)
        flask_app.test_client().get('/flickr/')
        flickr_oauth.oauth.authorize.assert_called_with(callback='/flickr/oauth-authorized')


    def test_flickr_get_flickr_token_returns_None_if_no_token(self):
        from pybossa.view.flickr import get_flickr_token
        with flask_app.test_request_context():
            token = get_flickr_token()

        assert token is None, token


    def test_flickr_get_flickr_token_returns_existing_token(self):
        from pybossa.view.flickr import get_flickr_token
        with flask_app.test_request_context():
            session['flickr_token'] = 'fake_token'
            token = get_flickr_token()

        assert token is 'fake_token', token


    def test_logout_removes_token_and_user_from_session(self):
        with flask_app.test_client() as c:
            with c.session_transaction() as sess:
                sess['flickr_token'] = 'fake_token'
                sess['flickr_user'] = 'fake_user'

                assert 'flickr_token' in sess
                assert 'flickr_user' in sess

            c.get('/flickr/revoke-access')

            assert 'flickr_token' not in session
            assert 'flickr_user' not in session


    @patch('pybossa.view.flickr.redirect')
    def test_logout_redirects_to_url_specified_by_next_param(self, redirect):
        redirect.return_value = Response(302)
        flask_app.test_client().get('/flickr/revoke-access?next=http://mynext_url')

        redirect.assert_called_with('http://mynext_url')


    @patch('pybossa.view.flickr.flickr')
    def test_oauth_authorized_adds_token_and_user_to_session(self, flickr_oauth):
        fake_resp = {'oauth_token_secret': u'secret',
                     'username': u'palotespaco',
                     'fullname': u'paco palotes',
                     'oauth_token':u'token',
                     'user_nsid': u'user'}
        flickr_oauth.oauth.authorized_response.return_value = fake_resp

        with flask_app.test_client() as c:
            c.get('/flickr/oauth-authorized')
            flickr_token = session.get('flickr_token')
            flickr_user = session.get('flickr_user')

        assert flickr_token == {'oauth_token_secret': u'secret', 'oauth_token': u'token'}
        assert flickr_user == {'username': u'palotespaco', 'user_nsid': u'user'}


    @patch('pybossa.view.flickr.flickr')
    @patch('pybossa.view.flickr.redirect')
    def test_oauth_authorized_redirects_to_url_specified_by_next_param(
            self, redirect, flickr_oauth):
        fake_resp = {'oauth_token_secret': u'secret',
                     'username': u'palotespaco',
                     'fullname': u'paco palotes',
                     'oauth_token':u'token',
                     'user_nsid': u'user'}
        flickr_oauth.oauth.authorized_response.return_value = fake_resp
        redirect.return_value = Response(302)
        flask_app.test_client().get('/flickr/oauth-authorized?next=http://next')

        redirect.assert_called_with('http://next')


    @patch('pybossa.view.flickr.flickr')
    @patch('pybossa.view.flickr.redirect')
    def test_oauth_authorized_user_refused_to_login_flickr(
            self, redirect, flickr_oauth):
        flickr_oauth.oauth.authorized_response.return_value = None
        redirect.return_value = Response(302)
        flask_app.test_client().get('/flickr/oauth-authorized?next=http://next')

        redirect.assert_called_with('http://next')


    @patch.object(Flickr, 'oauth')
    def test_get_own_albums_return_empty_list_on_request_error(self, oauth):
        class Res(object):
            pass
        response = Res()
        response.status = 404
        response.data = 'not found'
        oauth.get.return_value = response
        token = {'oauth_token_secret': u'secret', 'oauth_token': u'token'}
        user = {'username': u'palotespaco', 'user_nsid': u'user'}

        flickr = Flickr()
        flickr.app = MagicMock()

        with flask_app.test_request_context():
            session['flickr_token'] = token
            session['flickr_user'] = user
            albums = flickr.get_own_albums()

        assert albums == [], albums


    @patch.object(Flickr, 'oauth')
    def test_get_own_albums_return_empty_list_on_request_fail(self, oauth):
        class Res(object):
            pass
        response = Res()
        response.status = 200
        response.data = {'stat': 'fail', 'code': 1, 'message': 'User not found'}
        oauth.get.return_value = response
        token = {'oauth_token_secret': u'secret', 'oauth_token': u'token'}
        user = {'username': u'palotespaco', 'user_nsid': u'user'}

        flickr = Flickr()
        flickr.app = MagicMock()

        with flask_app.test_request_context():
            session['flickr_token'] = token
            session['flickr_user'] = user
            albums = flickr.get_own_albums()

        assert albums == [], albums


    @patch.object(Flickr, 'oauth')
    def test_get_own_albums_log_response_on_request_fail(self, oauth):
        class Res(object):
            pass
        response = Res()
        response.status = 200
        response.data = {'stat': 'fail', 'code': 1, 'message': 'User not found'}
        oauth.get.return_value = response
        token = {'oauth_token_secret': u'secret', 'oauth_token': u'token'}
        user = {'username': u'palotespaco', 'user_nsid': u'user'}
        log_error_msg = ("Bad response from Flickr:\nStatus: %s, Content: %s"
            % (response.status, response.data))

        flickr = Flickr()
        flickr.app = MagicMock()

        with flask_app.test_request_context():
            session['flickr_token'] = token
            session['flickr_user'] = user
            albums = flickr.get_own_albums()
            flickr.app.logger.error.assert_called_with(log_error_msg)


    @patch.object(Flickr, 'oauth')
    def test_get_own_albums_return_list_with_album_info(self, oauth):
        class Res(object):
            pass
        response = Res()
        response.status = 200
        response.data = {
            u'stat': u'ok',
            u'photosets': {
                u'total': 2,
                u'perpage': 2,
                u'photoset':
                [{u'date_update': u'1421313791',
                  u'visibility_can_see_set': 1,
                  u'description': {u'_content': u'mis mejores vacaciones'},
                  u'videos': 0, u'title': {u'_content': u'vacaciones'},
                  u'farm': 9, u'needs_interstitial': 0,
                  u'primary': u'16284868505',
                  u'primary_photo_extras': {
                      u'height_t': u'63',
                      u'width_t': u'100',
                      u'url_t': u'https://farm9.staticflickr.com/8597/16284868505_c4a032a62e_t.jpg'},
                  u'server': u'8597',
                  u'date_create': u'1421313790',
                  u'photos': u'3',
                  u'secret': u'c4a032a62e',
                  u'count_comments': u'0',
                  u'count_views': u'1',
                  u'can_comment': 0,
                  u'id': u'72157649886540037'}],
                u'page': 1,
                u'pages': 1}}
        oauth.get.return_value = response
        token = {'oauth_token_secret': u'secret', 'oauth_token': u'token'}
        user = {'username': u'palotespaco', 'user_nsid': u'user'}

        with flask_app.test_request_context():
            session['flickr_token'] = token
            session['flickr_user'] = user
            albums = Flickr().get_own_albums()

        expected_album = response.data['photosets']['photoset'][0]
        expected_album_info = {
            'photos': expected_album['photos'],
            'thumbnail_url': expected_album['primary_photo_extras']['url_t'],
            'id': expected_album['id'],
            'title': expected_album['title']['_content']}

        assert albums == [expected_album_info], albums
