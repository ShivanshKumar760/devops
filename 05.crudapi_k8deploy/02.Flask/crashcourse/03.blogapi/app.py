from flask import Flask , jsonify , request 
from flask_jwt_extended import JWTManager , create_access_token , jwt_required , get_jwt_identity
import os

app = Flask(__name__)
app.config["JWT_SECRET_KEY"]=os.getenv('SECRET_KEY') # this is the secret key which will be used to sign the JWT token and it should be kept secret and should not be hardcoded in the code
jwt=JWTManager(app)



users_db=[
    {
        "id":1,
        "username":"john",
        "password":"password123"
    },
    {
        "id":2,
        "username":"jane",
        "password":"password456"
    }
]

blog_db=[
    {
        "id":1,
        "title":"First Blog Post",
        "content":"This is the content of the first blog post.",
        "author_id":1
    }
]
#Creating a access token 
@app.route('/login' , methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username' , '')
    password = data.get('password' , '')
    user = next((u for u in users_db if u['username']== username and u['password']== password), None)
    if user is None:
        return jsonify({"error":"Invalid credentials"}), 401
    access_token = create_access_token(identity=str(user['id']))
    return jsonify({"access_token": access_token})


#Creating a protected route
@app.route('/protected' , methods=['GET'])
@jwt_required()
def protected():
    current_user_id = get_jwt_identity() # this will basically decode the JWT token and return the identity which we set while creating the token in login function which is user['id']
    # converting current_user_id to int because we stored it as string in the token and we need to compare it with the id in the users_db which is an integer
    current_user_id=int(current_user_id)
    user = next((u for u in users_db if u['id']== current_user_id), None)
    return jsonify({"message": f"Hello, {user['username']}! This is a protected route."})


@app.route('/blogs' , methods=['POST'])
@jwt_required()
def create_blog():
    current_user_id = get_jwt_identity()
    current_user_id = int(current_user_id)
    data = request.get_json()
    title = data.get('title' , '')
    content = data.get('content' , '')
    if not title or not content:
        return jsonify({"error":"Title and content are required"}), 400
    blog = {
        "id": len(blog_db) + 1,
        "title": title,
        "content": content,
        "author_id": current_user_id
    }
    blog_db.append(blog)

    return jsonify(blog) , 201

@app.route('/blogs' , methods=['GET'])
def get_blogs():
    return jsonify(blog_db)

@app.route('/blogs/<int:blog_id>' , methods=['GET'])
def get_blog(blog_id):
    blog = next((b for b in blog_db if b['id']== blog_id), None)
    if blog is None:
        return jsonify({"error":"Blog not found"}), 404
    return jsonify(blog)

@app.route('/blogs/<int:blog_id>' , methods=['DELETE'])
@jwt_required()
def delete_blog(blog_id):
    global blog_db
    current_user_id = get_jwt_identity()
    current_user_id = int(current_user_id)
    blog = next((b for b in blog_db if b['id']== blog_id), None)
    if blog is None:
        return jsonify({"error":"Blog not found"}), 404
    if blog['author_id'] != current_user_id:
        return jsonify({"error":"You are not authorized to delete this blog"}), 403
    blog_db = [b for b in blog_db if b['id'] != blog_id]
    return jsonify({"message":"Blog deleted successfully"})


if __name__ == '__main__':
    app.run(debug=True) 