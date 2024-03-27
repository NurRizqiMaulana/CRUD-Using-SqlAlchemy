from flask import Flask
from markupsafe import escape
from flask import request
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from flask import jsonify


class Base(DeclarativeBase): 
    pass #Blank body class, but "Base" class inherits "DeclarativeBase" class

app = Flask(__name__) # Instantiate Flask
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql://root:@127.0.0.1/myflask"  #"mysql://username:password@localhost/databasename"  
db = SQLAlchemy(model_class=Base) # Instantiate SQLALchemy
db.init_app(app)

class User(db.Model): #User class inherit Model class
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(unique=True)
    name: Mapped[str]

@app.route("/user", methods=['GET','POST','PUT','DELETE'])
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