from flask import Flask
from markupsafe import escape
from flask import request
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from flask import jsonify
import base64

from argon2 import PasswordHasher

from datetime import datetime
from datetime import timedelta
from datetime import timezone

from flask_jwt_extended import create_access_token
from flask_jwt_extended import current_user
from flask_jwt_extended import get_jwt_identity
from flask_jwt_extended import jwt_required
from flask_jwt_extended import JWTManager


class Base(DeclarativeBase): 
    pass #Blank body class, but "Base" class inherits "DeclarativeBase" class

app = Flask(__name__) # Instantiate Flask
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql://root:@127.0.0.1/myflask"  #"mysql://username:password@localhost/databasename"  
db = SQLAlchemy(model_class=Base) # Instantiate SQLALchemy
db.init_app(app)

# Setup the Flask-JWT-Extended extension
app.config["JWT_SECRET_KEY"] = "super-secret"  # Change this!
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(days=1)
jwt = JWTManager(app)

class User(db.Model): #User class inherit Model class
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(unique=True)
    name: Mapped[str]
    password: Mapped[str]

class ApiKey(db.Model): #User class inherit Model class
    api_key: Mapped[str] = mapped_column(primary_key=True)

# @jwt.user_identity_loader
# def user_identity_lookup(user):
#     return user.id

# @jwt.user_lookup_loader
# def user_lookup_callback(_jwt_header, jwt_data):
#     id = jwt_data["sub"]
#     return User.query.filter_by(id=id).one_or_none()

@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    identity = jwt_data["sub"]
    return User.query.filter_by(id=identity).one_or_none()

@app.route("/user", methods=['GET','POST','PUT','DELETE'])
@jwt_required()
def user():
    if request.method == 'POST':
        dataDict = request.get_json() #It return dictionary.
        email = dataDict["email"]
        name = dataDict["name"]
        user = User(
            email= email,
            name = name,
        )
        db.session.add(user)
        db.session.commit()
        
        return {
            "message": "Successfull",
            "data": f"email: {email}, name : {name}"
        }, 200 
        
        
    elif request.method == 'PUT':
        dataDict = request.get_json() #It return dictionary.
        id = dataDict["id"]
        email = dataDict["email"]
        name = dataDict["name"]
        
        if not id:
            return {
                "message": "ID required"
            },400
        
        row = db.session.execute(
            db.select(User) #Select from user model
            .filter_by(id=id) #where ID=1  by id
            ).scalar_one() # Return a list of rows.
        if "email" in dataDict : 
            row.email = dataDict["email"]
            
        if "name" in dataDict :
            row.name = dataDict["name"]
        db.session.commit()
        return {
            "message": "Successfull!"
        }, 200
    elif request.method == 'DELETE':
        dataDict = request.get_json() #It return dictionary.
        id = dataDict["id"]
        
        if not id:
            return {
                "message": "ID required"
            },400
        
        row = db.session.execute(
            db.select(User) #Select from user model
            .filter_by(id=id) #where ID=1  by id
            ).scalar_one() # Return a list of rows.
        
        db.session.delete(row)
        db.session.commit()
        return {
            "message": "Successfull!"
        }, 200
    else : #GET
        rows = db.session.execute(
            db.select(User).order_by(User.id)
            ).scalars()
        
        users =[]
        for row in rows:
            users.append({
                "id" : row.id,
                "email" : row.email,
                "name" : row.name,
            })
        return users, 200
        

@app.post('/signup')
def signup():
    dataDict = request.get_json() # Mendapatkan data JSON dari request
    name = dataDict["name"]
    email = dataDict["email"]
    password = dataDict["password"]
    re_password = dataDict["re_password"]
    
    # Memeriksa apakah password sama dengan re_password
    if password != re_password:
        return {
            "message" : "Password tidak sama!"
        }, 400
    
    # Memeriksa apakah email terisi
    if not email:
        return {
            "message" : "Email harus diisi"
        }, 400
        
    # Menghash password menggunakan Argon2
    hashed_password = PasswordHasher().hash(password)
    # Membuat objek User dengan menggunakan properti yang sesuai
    new_user = User(
        email=email,
        name=name,
        password=hashed_password,  # Pastikan properti ini sesuai dengan definisi model
    )
    db.session.add(new_user)
    db.session.commit()
    
    return {
        "message" : "Successfully"
    },201   
        
    

@app.post("/sigin")
def sigin():
    #catch the Authorization header
    base64Str = request.headers.get('Authorization')
    base64Str = base64Str[6:] # hapus "Basic" string
    
    #Mulai Base64 Decode
    base64Bytes = base64Str.encode('ascii')
    messageBytes = base64.b64decode(base64Bytes)
    pair = messageBytes.decode('ascii')
    #Akhir Base64 Decode
    
    email, password = pair.split(":")
    
    user = db.session.execute(
        db.select(User)
        .filter_by(email=email)
    ).scalar_one()
    if not user or not PasswordHasher().verify(user.password, password):
        return {
            "message": "wrong password or email!"
        },400
    #End Authentication    
    
    #Start Generate JWT Token
    access_token = create_access_token(identity=user.id)
    #End Generate JWT Token
    return {
        "token_access" : access_token,
    },200
    
@app.post("/login")
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return {
            "message": "Email dan kata sandi diperlukan!"
        }, 400
    user = db.session.execute(
        db.select(User)
        .filter_by(email=email)
    ).scalar_one() 
    
    if not user or not PasswordHasher().verify(user.password, password):
        return {
            "message": "Email atau kata sandi salah!"
        }, 400
    
    # Autentikasi berhasil, generate token akses JWT
    access_token = create_access_token(identity=user.id)
    
    return {
        "token_access": access_token
    }, 200
    
    
    
@app.get("/myprofile")
@jwt_required()
def profile():
    current_user = get_jwt_identity()
    
    return {
        "id" : current_user.id,
        "email" : current_user.email,
        "name" : current_user.name,
        
    }

@app.get("/who")
@jwt_required()
def protected():
    # We can now access our sqlalchemy User object via `current_user`.
    return jsonify(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
    )
# @app.route("/")
# def hello_world():
#     return {
#             "message":"Hellow"
#             },200

# @app.route('/hello')
# def hello():
#     return {
#             "message":"Hello, world!"
#             },200
    
# @app.route('/user/<username>')
# def show_user_profile(username):
#     # show the user profile for that user
#     return {
#             "message":f"Hello, {username}!"
#             },200

# @app.route('/post/<int:post_id>')
# def show_post(post_id):
#     # show the post with the given id, the id is an integer
#     return f'Post {post_id}'

# @app.route('/path/<path:subpath>')
# def show_subpath(subpath):
#     # show the subpath after /path/
#     return f'Subpath {escape(subpath)}'

# from flask import request

# @app.route('/upload', methods=['GET','POST'])
# def upload_file():
#     if request.method =='POST':
#         f = request.files['image']
#         f.save('image.jpg')
#     return {
#             "message" : "success"
#     },200