import pytest
from flask import g, session
from flaskr.db import get_db

#test that register render on GET and on POST it should store valid form data and redirect
def test_register(client, app):
    #make a get request and and assert the Response object
    assert client.get('/auth/register').status_code == 200
    #make POST request and convert the data to a dict
    response = client.post(
        #data containt the body of the response as bytes
        '/auth/register', data={'username': 'a', 'password': 'a'}
    )
    assert 'http://localhost/auth/login' == response.headers['Location']

    with app.app_context():
        assert get_db().execute(
            "SELECT * FROM user WHERE username = 'a'"
        ).fetchone() is not None

#@pytest.mark.parametrize tellt Pytest to run the same test function with
#different arguements
#we use it to test 3 different inputs
@pytest.mark.parametrize(('username', 'password', 'message'), (
    ('', '', b'Username is required'),
    ('a', '', b'Password is required.'),
    ('test', 'test', b'already registered')
))
def test_register_validate_input(client, username, password, message):
    response = client.post(
        '/auth/register',
        data={'username': username, 'password': password}
    )
    assert message in response.data

#test login, very similar to the register test
#session should have user_id set after logging in
def test_login(client, auth):
    assert client.get('/auth/login').status_code == 200
    response = auth.login()
    assert response.headers['Location'] == 'http://localhost/'

    with client:
        client.get('/')
        assert session['user_id'] == 1
        assert g.user['username'] == 'test'

@pytest.mark.parametrize(('username', 'password', 'message'),(
    ('a', 'test', b'Incorrect username.'),
    ('test', 'a', b'Incorrect password.')
))
def test_login_validate_input(auth, username, password, message):
    response = auth.login(username, password)
    assert message in response.data

# test logout is the opposite of login, should not return session
def test_logout(client, auth):
    auth.login()

    with client:
         auth.logout()
         assert 'user_id' not in session
