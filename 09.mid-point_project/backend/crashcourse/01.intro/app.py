from flask import Flask, jsonify , request

app = Flask(__name__)


#this is a get method 
@app.route('/hello')
def hello():
    return jsonify({
        "message":"Hello, World!"
    })


#this is a post method which will simply post a message and we will respond with that
#same messsage

@app.route('/echo' , methods=['POST'])
def echo():
    data = request.get_json()
    message = data.get('message' , '')
    return jsonify({
        "echo": message
    })

# let create a in memory database to store some data   
users = []

@app.route('/users' , methods=['POST'])
def create_user():
    data= request.get_json()
    name= data.get('name' , '')
    if not name:
        return jsonify({"error":"Name is required"}), 400
    user = {
        "id": len(users) + 1,
        "name": name
    }
    users.append(user)
    return jsonify(user) , 201

@app.route('/users' , methods=['GET'])
def get_users():
    return jsonify(users)

@app.route('/users/<int:user_id>' , methods=['GET'])
def get_user(user_id):
    user = next((u for u in users if u['id']== user_id), None)
    if user is None:
        return jsonify({"error":"User not found"}), 404
    return jsonify(user)

@app.route('/users/<int:user_id>' , methods=['DELETE'])
def delete_user(user_id):
    global users # why global ? because we are modifying the users list which is defined outside the function scope
    # but why can't we just refer users without global ? because if we try to modify users without global it will create a new local variable users inside the function scope and it will not affect the global users list

    #then why didnt we used global in above get_user function ? because we are not modifying the users list in get_user function we are just reading it and reading a global variable is allowed without global keyword but modifying it requires global keyword
    user = next((u for u in users if u['id']== user_id), None)
    #what is next # next is a built in function in python which returns the next item from the iterator and if there is no next item it returns the default value which is None in our case
    #what will it look like without next 
    # user = None
    # for u in users:
    #     if u['id'] == user_id:
    #         user = u
    if user is None:
        return jsonify({"error":"User not found"}), 404
    users = [u for u in users if u['id'] != user_id]
    return jsonify({"message":"User deleted successfully"})

@app.route('/users/<int:user_id>' , methods=['PUT'])
def update_user(user_id):
    global users
    data = request.get_json()
    name = data.get('name' , '')
    if not name:
        return jsonify({"error":"Name is required"}), 400
    user = next((u for u in users if u['id']== user_id), None)
    if user is None:
        return jsonify({"error":"User not found"}), 404
    user['name'] = name
    return jsonify(user)

if __name__ == '__main__':
    app.run(debug=True) 