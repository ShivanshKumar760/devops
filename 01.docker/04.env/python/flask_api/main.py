from flask import Flask , jsonify
import os , socket

app = Flask(__name__)

ENV = os.getenv('ENV_VALUE' , 'No env set')
HOSTNAME = socket.gethostname()

@app.get('/')
def hello():
    return jsonify({
        'message' : 'Hello World',
        'env' : ENV,
        'hostname' : HOSTNAME
    })

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=3000)