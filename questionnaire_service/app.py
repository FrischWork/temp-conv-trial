from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import scoped_session, sessionmaker
import cryptography
from confluent_kafka import Consumer, Producer, KafkaError, KafkaException
import threading
import logging
import sys
import json

app = Flask(__name__)

# Configuration for SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:password@questionnaire-db:3306/convenienttrial'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Create a configured "Session" class and a scoped session factory
session_factory = sessionmaker(bind=db.engine)
Session = scoped_session(session_factory)

logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define Message model
class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.Text, nullable=False)

conf = {
    'bootstrap.servers': 'kafka:9092',
    'group.id': 'my_group',
    'auto.offset.reset': 'earliest'
}

def handle_posts():
    consumer = Consumer(conf)
    consumer.subscribe(['test_topic'])
    while True:
        db_session = Session()
        msg = consumer.poll(1.0)
        if msg is None:
            continue
        if msg.error():
            if msg.error().code() == KafkaError._PARTITION_EOF:
                continue
            else:
                print(msg.error())
                break
        logging.info(f">> receieved msg: {msg.value()}")
        logging.info(f">> receieved err: {msg.error()}")
        data = json.loads(msg.value().decode('utf-8'))
        logging.info(f">> We received {data}")
        new_message = Message(message=data["message"])


        messages = db_session.query(Message).all()
        logging.info(f"SANITY")
        logging.info(f">>>> Messages before: {len(messages)}")

        db_session.add(new_message)
        db_session.commit()
        logging.info(f">> message stored: {data['message']}")

        messages = db_session.query(Message).all()
        logging.info(f">>>> Messages after: {len(messages)}")
        db_session.close()

def handle_gets():
    consumer = Consumer(conf)
    producer = Producer(conf)

    consumer.subscribe(['messages_requests'])

    while True:
        msg = consumer.poll(1.0)
        db_session = Session()
        if msg is None:
            continue
        if msg.error():
            if msg.error().code() == KafkaError._PARTITION_EOF:
                continue
            else:
                raise KafkaException(message.error())
        request = json.loads(msg.value().decode('utf-8'))
        query_id = request['query_id']

        messages = db_session.query(Message).all()
        data = [{'id': msg.id, 'message': msg.message} for msg in messages]

        response = {'query_id': query_id, 'data': data}
        producer.produce('messages_responses', key=query_id, value=json.dumps(response))
        producer.flush()
        logging.info(f">> sent {len(messages)} messages")
        db_session.close()

        #new_message = Message(message=msg.value())
        #db.session.add(new_message)
        #db.session.commit()


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

    post_thread = threading.Thread(target=handle_posts)
    post_thread.start()

    get_thread = threading.Thread(target=handle_gets)
    get_thread.start()

    app.run(host='0.0.0.0', port=8000, debug=True)

