from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
import requests
import json
import os
import sys
import uuid
import time
from confluent_kafka import Producer, Consumer, KafkaException, KafkaError

authentication_service_url = os.getenv('AUTHENTICATION_SERVICE_URL')
encryption_service_url = os.getenv('ENCRYPTION_SERVICE_URL')
questionnaire_service_url = os.getenv('QUESTIONNAIRE_SERVICE_URL')

app = Flask(__name__)
CORS(app)

logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

producer = Producer({
    'bootstrap.servers': 'kafka:9092'
})
consumer = Consumer({
    'bootstrap.servers': 'kafka:9092',
    'group.id': 'my_group',
    'auto.offset.reset': 'earliest'
})

def delivery_report(err, msg):
    if err is not None:
        logger.error(f"Error: {err}")
    else:
        logger.info('Message delivered to {} [{}]'.format(msg.topic(), msg.partition()))


def send_query_request():
    logger.info(f"sending query...")
    query_id = str(uuid.uuid4())
    logger.info(">> query_id: %s" % query_id)
    producer.produce('messages_requests', key=query_id, value=json.dumps({"query_id": query_id}), callback=delivery_report)
    logger.info(f">> produced message")
    producer.flush()
    logger.info(f">> flushed")
    return query_id

def get_query_response(query_id, timeout=60):
    logger.info(f"waiting for response to query_id: {query_id}")
    consumer = Consumer({
        'bootstrap.servers': 'kafka:9092',
        'group.id': 'my_group',
        'auto.offset.reset': 'earliest'
    })
    consumer.subscribe(['messages_responses'])
    end_time = time.time() + timeout
    while time.time() < end_time:
        msg = consumer.poll(timeout=0.5)
        if msg is None:
            logger.info(">> ... still waiting ... ")
            continue
        if msg.error():
            if msg.error().code() == KafkaError._PARTITION_EOF:
                continue
            else:
                logger.info(">> Horribly bad stuff happened")
                raise KafkaException(msg.error())
        response = json.loads(msg.value().decode('utf-8'))
        if response['query_id'] == query_id:
            logger.info(f">> found response: {response}")
            logger.info(f">>>> response messages: {response['data']}")
            consumer.close()
            return response['data']
    consumer.close()
    logger.info(">> Failed finding message")
    raise TimeoutError('Timeout waiting for query response')

@app.route('/health', methods=['GET'])
def health_check():
    logger.info("starting health check")
    missing_services = []

    # check authentication connection
    if authentication_service_url:
        health_url = f"{authentication_service_url.rstrip('/')}/health"
        logger.info(f">> authentication health url: {health_url}")

        try:
            response = requests.get(health_url)
            if not response.status_code == 200:
                logger.info(f">> authentication service health: {response.status_code}")
                missing_services.append("Authentication Service")
        except requests.RequestException as e:
            logger.info(f">> authentication service health: {e}")
            missing_services.append("Authentication Service")
    else:
        logger.info(">> no authentication url")
        missing_services.append("Authentication Service")

    # check encryption connection
    if encryption_service_url:
        health_url = f"{encryption_service_url.rstrip('/')}/health"
        logger.info(f">> encryption health url: {health_url}")

        try:
            response = requests.get(health_url)
            if not response.status_code == 200:
                logger.info(f">> encryption service health: {response.status_code}")
                missing_services.append("Encryption Service")
        except requests.RequestException as e:
            logger.info(f">> encryption service health: {e}")
            missing_services.append("Encryption Service")
    else:
        logger.info(">> no encryption url")
        missing_services.append("Encryption Service")

    # check questionnaire connection
    if questionnaire_service_url:
        health_url = f"{questionnaire_service_url.rstrip('/')}/health"
        logger.info(f">>  questionnaire health url: {health_url}")

        try:
            response = requests.get(health_url)
            if not response.status_code == 200:
                logger.info(f">> questionnaire service health: {response.status_code}")
                missing_services.append("Questionnaire Service")
        except requests.RequestException as e:
            logger.info(f">> questionnaire service health: {e}")
            missing_services.append("Questionnaire Service")
    else:
        logger.info(">> no questionnaire url")
        missing_services.append("Questionnaire Service")


    if len(missing_services) > 0:
        logger.info("health check failed due to missing dependencies")
        return jsonify({"error": "missing dependencies", "details": missing_services}), 500

    return "success", 200


@app.route('/messages', methods=['POST'])
def add_message():
    message_text = request.json.get('message')
    logger.info(f"<< message is now: {message_text}")

    if not message_text:
        return jsonify({"error": "No message provided"}), 400

    # authenticate and authorize the request
    try:
        authentication_url = f"{authentication_service_url.rstrip('/')}/authenticate"
        response = requests.post(authentication_url, json={"message": message_text})
        if not response.status_code == 200:
            return jsonify({}), response.status_code
        message_text = response.json()['message']
        logger.info(f"<< message is now: {message_text}")
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    # encrypt the message
    try:
        encryption_url = f"{encryption_service_url.rstrip('/')}/encrypt"
        response = requests.post(encryption_url, json={"message": message_text})
        if not response.status_code == 201:
            return jsonify({}), response.status_code
        message_text = response.json()['message']
        logger.info(f"<< message is now: {message_text}")
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    # attempt to communicate with the questionnaire service
    #try:
    #    messages_url = f"{questionnaire_service_url.rstrip('/')}/messages"
    #    logger.info(f"Sending message request with text '{message_text}'")
    #    logger.info(f">> using URL: {messages_url}")
    #    logger.info(f">> data type: {type(message_text)}")
    #    response = requests.post(messages_url, json={"message": message_text})
    #    logger.info(f">> response code: {response.status_code}")
    #    if not response.status_code == 200:
    #        return jsonify(response.json()), response.status_code
    #    return jsonify(response.json()), 200
    #except Exception as e:
    #    logger.info(">> Something went horribly wrong :(")
    #    return jsonify({"error": str(e)}), 500

    query_id = str(uuid.uuid4())
    data = { 'query_id': query_id, 'message': message_text }
    producer.produce('test_topic', key=query_id, value=json.dumps(data))
    producer.flush()
    return jsonify({"status": "Message sent"}), 200

@app.route('/messages', methods=['GET'])
def get_messages():
    logger.info("FLUTTERSHY: MAIN")
    try:
        logger.info("<< starting")
        query_id = send_query_request()
        logger.info("<< request sent")
        messages = get_query_response(query_id)
        logger.info("<< response received")
        return jsonify({'messages': messages}), 200
    except Exception as e:
        logger.info(f"ERROR: {e}")
        return jsonify({"error": str(e)}), 500

    #try:
    #    messages_url = f"{questionnaire_service_url.rstrip('/')}/messages"
    #    response = requests.get(messages_url)
    #    if not response.status_code == 200:
    #        return jsonify({}), response.status_code
    #    return jsonify(response.json()), 200
    #except Exception as e:
    #    return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)

