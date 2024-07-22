from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import cryptography

app = Flask(__name__)

# Configuration for SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:password@questionnaire-db:3306/convenienttrial'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Define Message model
class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.Text, nullable=False)

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({}), 200

@app.route('/messages', methods=['POST'])
def add_message():
    try:
        # Get message from POST request
        message_text = request.json.get('message')

        if not message_text:
            return jsonify({"error": "No message provided"}), 400

        # Create a new Message record
        new_message = Message(message=message_text)
        db.session.add(new_message)
        db.session.commit()

        return jsonify({"status": "Message added", "message": message_text}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/messages', methods=['GET'])
def get_messages():
    try:
        # Query all messages
        messages = Message.query.all()
        messages_list = [{'id': msg.id, 'message': msg.message} for msg in messages]

        return jsonify(messages_list), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Create tables
    with app.app_context():
        db.create_all()

    app.run(host='0.0.0.0', port=8000, debug=True)

