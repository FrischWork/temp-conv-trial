from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import uuid
import secrets
import string
import cryptography

app = Flask(__name__)

# Configuration for SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:password@authentication-db:3308/convenienttrial'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Define Encryption model
class Authentication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Text, nullable=False)
    access_token = db.Column(db.Text, nullable=False)


@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({}), 200

@app.route('/authenticate', methods=['POST'])
def authenticate():
    try:
        # Get message from POST request
        message_text = request.json.get('message')

        if not message_text:
            return jsonify({"error": "No message provided"}), 400

        # Create a new Encryption record
        return jsonify({"message": "authenticated(%s)"%message_text}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Create tables
    with app.app_context():
        db.create_all()

    app.run(host='0.0.0.0', port=8000, debug=True)

