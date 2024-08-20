from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)

# MySQL configuration with SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@127.0.0.1:3306/flask_app'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    mobile = db.Column(db.String(20), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    tags = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    published = db.Column(db.Boolean, default=False)
    likes = db.Column(db.Integer, default=0)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('posts', lazy=True))

# 1. User signup
@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    print(data)  # Log the incoming data for debugging

    # Ensure all required keys are present
    required_keys = ['name', 'email', 'mobile', 'username', 'password']
    for key in required_keys:
        if key not in data:
            return jsonify({'message': f'Missing required key: {key}'}), 400

    user = User.query.filter_by(username=data['username']).first()
    if user:
        return jsonify({'message': 'Username already exists'}), 400
    if len(data['password']) < 8:
        return jsonify({'message': 'Password must be at least 8 characters'}), 400
    hashed_password = generate_password_hash(data['password'])
    new_user = User(name=data['name'], email=data['email'], mobile=data['mobile'], username=data['username'], password=hashed_password)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'User created successfully'}), 201

# 2. User Login
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(username=data['username']).first()
    if not user:
        return jsonify({'message': 'Username not found'}), 404
    if not check_password_hash(user.password, data['password']):
        return jsonify({'message': 'Invalid password'}), 401
    return jsonify({'message': 'User logged in successfully'}), 200

# 3. Create a post
@app.route('/post', methods=['POST'])
def create_post():
    data = request.get_json()
    user = User.query.filter_by(username=data['username']).first()
    if not user:
        return jsonify({'message': 'Invalid username'}), 401
    new_post = Post(title=data['title'], description=data['description'], tags=data['tags'], user_id=user.id)
    db.session.add(new_post)
    db.session.commit()
    return jsonify({'message': 'Post created successfully'}), 201

# 4. Publish/Un-publish post
#publish post


@app.route('/post/<int:post_id>/publish', methods=['PUT'])
def publish_post(post_id):
    post = Post.query.get(post_id)
    if not post:
        return jsonify({'message': 'Post not found'}), 404
    
    if post.published:
        return jsonify({'message': 'Post is already published'}), 400
    
    post.published = True
    db.session.commit()
    return jsonify({'message': 'Post published successfully'}), 200


#unpublish post


@app.route('/post/<int:post_id>/unpublish', methods=['PUT'])
def unpublish_post(post_id):
    post = Post.query.get(post_id)
    if not post:
        return jsonify({'message': 'Post not found'}), 404
    
    if not post.published:
        return jsonify({'message': 'Post is already unpublished'}), 400
    
    post.published = False
    db.session.commit()
    return jsonify({'message': 'Post unpublished successfully'}), 200



# 5. List posts
@app.route('/posts', methods=['GET'])
def list_posts():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    posts_query = Post.query.filter_by(published=True).paginate(page=page, per_page=per_page, error_out=False)

    posts = posts_query.items
    return jsonify([{
        'id': post.id,
        'title': post.title,
        'description': post.description,
        'tags': post.tags,
        'created_at': post.created_at.isoformat(),  # Formatting datetime as ISO string
        'published': post.published,
        'likes': post.likes
    } for post in posts]), 200

# 6. Like/Un-like post
@app.route('/post/<int:post_id>/like', methods=['PUT'])
def like_post(post_id):
    post = Post.query.get(post_id)
    if not post:
        return jsonify({'message': 'Post not found'}), 404
    post.likes += 1
    db.session.commit()
    return jsonify({'message': 'Post liked successfully'}), 200

@app.route('/post/<int:post_id>/unlike', methods=['PUT'])
def unlike_post(post_id):
    post = Post.query.get(post_id)
    if not post:
        return jsonify({'message': 'Post not found'}), 404
    post.likes -= 1
    db.session.commit()
    return jsonify({'message': 'Post unliked successfully'}), 200

if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # Create tables in the database
    app.run(debug=True)
