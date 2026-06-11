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


if __name__ == '__main__':
    app.run(debug=True) 