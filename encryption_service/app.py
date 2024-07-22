from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import uuid
import secrets
import string
import cryptography

app = Flask(__name__)

# Configuration for SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:password@encryption-db:3307/convenienttrial'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Define Encryption model
class Encryption(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message_id = db.Column(db.Text, nullable=False)
    message_key = db.Column(db.Text, nullable=False)

def generate_random_string(length=40):
    # Define the characters you want to use
    characters = string.ascii_letters + string.digits
    # Generate a random string
    return ''.join(secrets.choice(characters) for _ in range(length))

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({}), 200

@app.route('/encrypt', methods=['POST'])
def encrypt_message():
    try:
        # Get message from POST request
        message_text = request.json.get('message')

        if not message_text:
            return jsonify({"error": "No message provided"}), 400

        # Create a new Encryption record
        new_encryption = Encryption(
            message_id = str(uuid.uuid4()),
            message_key = generate_random_string()
        )
        db.session.add(new_encryption)
        db.session.commit()

        return jsonify({"message": "encrypted(%s)"%message_text}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Create tables
    with app.app_context():
        db.create_all()

    app.run(host='0.0.0.0', port=8000, debug=True)

