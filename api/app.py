from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from models import db, User, File
from datetime import timedelta
import os
import sys
import logging
from werkzeug.utils import secure_filename
from pathlib import Path
import base64

# Configure logging to output to stdout
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, resources={r"/*": {
    "origins": "http://localhost:3333",
    "methods": ["GET", "POST", "OPTIONS", "PUT", "DELETE"],
    "allow_headers": ["Content-Type", "Authorization", "Access-Control-Allow-Credentials"],
    "supports_credentials": True
}})

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///files.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'your-secret-key'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=1)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize extensions
jwt = JWTManager(app)
db.init_app(app)

# Create uploads directory if it doesn't exist
Path(app.config['UPLOAD_FOLDER']).mkdir(parents=True, exist_ok=True)

# Create database tables
with app.app_context():
    db.create_all()


@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'message': 'Missing email or password'}), 400

    if User.query.filter_by(email=data['email']).first():
        return jsonify({'message': 'Email already registered'}), 400

    user = User(email=data['email'])
    user.set_password(data['password'])
    
    db.session.add(user)
    db.session.commit()
    
    return jsonify({'message': 'User registered successfully'}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'message': 'Missing email or password'}), 400

    user = User.query.filter_by(email=data['email']).first()
    
    if user and user.check_password(data['password']):
        access_token = create_access_token(identity=user.email)
        return jsonify({'access_token': access_token}), 200
    
    return jsonify({'message': 'Invalid email or password'}), 401

@app.route('/api/upload', methods=['POST'])
@jwt_required()
def upload_file():
    if 'file' not in request.files:
        logger.warning('Upload attempt with no file part')
        return jsonify({'message': 'No file part'}), 400
    
    file = request.files['file']
    url_path = request.form.get('url_path')

    ###
    # TODO: It's a good idea to use AI to read and summarize the file content.
    # Based on the summary, we can suggest a better structure to organize all files
    # as it can get a little messy when we have a lot of files. Also, we can suggest
    # meaningful insights to the user based on the other files in the folder.
    ###

    if not file or not url_path:
        logger.warning('Upload attempt with missing file or URL path')
        return jsonify({'message': 'Missing file or URL path'}), 400

    current_user_email = get_jwt_identity()
    current_user = User.query.filter_by(email=current_user_email).first()
    
    try:
        latest_file = File.query.filter_by(url_path=url_path)\
            .order_by(File.version.desc())\
            .first()
        
        next_version = 0 if latest_file is None else latest_file.version + 1
        
        filename = secure_filename(file.filename)
        storage_path = os.path.join(
            app.config['UPLOAD_FOLDER'],
            f"{hash(url_path)}_{next_version}_{filename}"
        )
        
        file.save(storage_path)
        
        new_file = File(
            url_path=url_path,
            filename=filename,
            version=next_version,
            storage_path=storage_path,
            mime_type=file.content_type,
            uploaded_by=current_user.id
        )
        
        db.session.add(new_file)
        db.session.commit()
        
        logger.info(f'File uploaded successfully: {url_path} (version {next_version})')
        return jsonify({
            'message': 'File uploaded successfully',
            'url': url_path,
            'version': next_version
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error during file upload: {str(e)}")
        return jsonify({'message': f'Upload failed: {str(e)}'}), 500

@app.route('/api/<path:file_path>')
@jwt_required()
def get_file(file_path):
    url_path = f'/{file_path}'
    revision = request.args.get('revision', type=int)

    logger.info(f"Getting file: {url_path} with revision: {revision}")

    current_user_email = get_jwt_identity()
    current_user = User.query.filter_by(email=current_user_email).first()
    
    newest_file = File.query\
        .filter_by(url_path=url_path)\
        .filter_by(uploaded_by=current_user.id)\
        .order_by(File.version.desc())\
        .first()
    
    if newest_file == None:
        return jsonify({'message': 'File not found'}), 404

    query = File.query.filter_by(url_path=url_path, uploaded_by=current_user.id)
    
    if revision is not None:
        file_record = query.filter_by(version=revision).first()
        if not file_record:
            return jsonify({'message': 'Revision not found'}), 404
    else:
        file_record = query.order_by(File.version.desc()).first()

    
    try:
        return jsonify({
            'file': {
                'data': base64.b64encode(open(file_record.storage_path, 'rb').read()).decode('utf-8'),
                'mimeType': file_record.mime_type,
                'filename': file_record.filename
            },
            'revision': {
                'current': file_record.version,
                'newest': newest_file.version
            }
        })
    except Exception as e:
        logger.error(f"Error serving file: {str(e)}")
        return jsonify({'message': 'Error serving file'}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5555) 