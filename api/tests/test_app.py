import pytest
import os
import io
import base64
from ..app import app, db
from ..models import User, File
from werkzeug.datastructures import FileStorage

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['UPLOAD_FOLDER'] = 'test_uploads'
    app.config['JWT_SECRET_KEY'] = 'test-secret'

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            # Create test user
            user = User(email='test@example.com')
            user.set_password('testpass')
            db.session.add(user)
            db.session.commit()
        yield client

    # Cleanup after tests
    with app.app_context():
        db.drop_all()

    if os.path.exists(app.config['UPLOAD_FOLDER']):
        for f in os.listdir(app.config['UPLOAD_FOLDER']):
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], f))
        os.rmdir(app.config['UPLOAD_FOLDER'])

@pytest.fixture
def auth_token(client):
    # Login to get JWT token
    response = client.post('/api/login', json={
        'email': 'test@example.com',
        'password': 'testpass'
    })
    return response.json['access_token']

def test_register(client):
    # Test successful registration
    response = client.post('/api/register', json={
        'email': 'new@example.com',
        'password': 'newpass'
    })
    assert response.status_code == 201
    
    # Test duplicate registration
    response = client.post('/api/register', json={
        'email': 'new@example.com',
        'password': 'newpass'
    })
    assert response.status_code == 400

def test_login(client):
    # Test valid login
    response = client.post('/api/login', json={
        'email': 'test@example.com',
        'password': 'testpass'
    })
    assert response.status_code == 200
    assert 'access_token' in response.json
    
    # Test invalid login
    response = client.post('/api/login', json={
        'email': 'test@example.com',
        'password': 'wrongpass'
    })
    assert response.status_code == 401

def test_upload_file(client, auth_token):
    # Test unauthorized upload
    response = client.post('/api/upload', data={})
    assert response.status_code == 401
    
    # Test valid upload
    headers = {'Authorization': f'Bearer {auth_token}'}
    data = {
        'file': (io.BytesIO(b'test content'), 'test.txt'),
        'url_path': '/test.txt'
    }
    response = client.post('/api/upload', 
        data=data,
        headers=headers,
        content_type='multipart/form-data'
    )

    assert response.status_code == 201
    assert response.json['version'] == 0
    
    # Test upload without file
    response = client.post('/api/upload', 
        data={'url_path': '/test.txt'},
        headers=headers,
        content_type='multipart/form-data'
    )
    assert response.status_code == 400

def test_get_file(client, auth_token):
    headers = {'Authorization': f'Bearer {auth_token}'}
    data = {
        'file': (io.BytesIO(b'test content'), 'test.txt'),
        'url_path': '/test.txt'
    }
    client.post('/api/upload', data=data, headers=headers, content_type='multipart/form-data')

    # Test get file
    response = client.get('/api/test.txt', headers=headers)
    assert response.status_code == 200
    assert response.json['file']['filename'] == 'test.txt'
    
    # Test get non-existent file
    response = client.get('/api/nonexistent.txt', headers=headers)
    assert response.status_code == 404 


def test_multiple_versions(client, auth_token):
    headers = {'Authorization': f'Bearer {auth_token}'}
    url_path = '/test.txt'
    
    # Upload 3 revisions
    for i in range(3):
        data = {
            'file': (io.BytesIO(f'content v{i}'.encode()), 'test.txt'),
            'url_path': url_path
        }
        response = client.post('/api/upload', 
            data=data,
            headers=headers,
            content_type='multipart/form-data'
        )
        assert response.status_code == 201
        assert response.json['version'] == i

    # Verify all revisions
    for i in range(3):
        response = client.get(f'/api/test.txt?revision={i}', headers=headers)
        assert response.status_code == 200
        assert base64.b64decode(response.json['file']['data']).decode() == f'content v{i}'
        assert response.json['revision']['current'] == i
        assert response.json['revision']['newest'] == 2  # Latest version

def test_user_file_isolation(client):
    # Create second user
    client.post('/api/register', json={
        'email': 'user2@example.com',
        'password': 'user2pass'
    })
    
    # Get tokens for both users
    token1 = client.post('/api/login', json={
        'email': 'test@example.com',
        'password': 'testpass'
    }).json['access_token']
    
    token2 = client.post('/api/login', json={
        'email': 'user2@example.com',
        'password': 'user2pass'
    }).json['access_token']

    # Both users upload same filename and path
    for token in [token1, token2]:
        headers = {'Authorization': f'Bearer {token}'}
        text = f'user specific content {token}'
        data = {
            'file': (io.BytesIO(text.encode('utf-8')), 'common.txt'),
            'url_path': '/common.txt'
        }
        response = client.post('/api/upload', 
            data=data,
            headers=headers,
            content_type='multipart/form-data'
        )
        assert response.status_code == 201

    # Verify each user can only access their own file
    for token in [token1, token2]:
        headers = {'Authorization': f'Bearer {token}'}
        response = client.get('/api/common.txt', headers=headers)
        text = f'user specific content {token}'
        assert response.status_code == 200
        assert base64.b64decode(response.json['file']['data']) == text.encode('utf-8')

    # Try to access other user's file
    response = client.get('/api/common.txt', headers={'Authorization': f'Bearer {token1}'})
    first_user_content = base64.b64decode(response.json['file']['data'])
    
    response = client.get('/api/common.txt', headers={'Authorization': f'Bearer {token2}'})
    second_user_content = base64.b64decode(response.json['file']['data'])
    
    # Should have different storage paths but same content
    assert first_user_content != second_user_content
    # But revisions should be independent
    assert client.get('/api/common.txt?revision=0', headers={'Authorization': f'Bearer {token1}'}).status_code == 200
    assert client.get('/api/common.txt?revision=0', headers={'Authorization': f'Bearer {token2}'}).status_code == 404 
