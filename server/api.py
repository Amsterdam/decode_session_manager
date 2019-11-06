import logging
import random
from threading import Lock

from flask import Flask, Response, json, request
from flask_cors import CORS
# from randomcolor import RandomColor # port of: https://github.com/davidmerfield/randomColor

import session_manager
from session_status import SessionStatus

app = Flask(__name__)
CORS(app)
lock = Lock() # because of race condition caused by WSGI in prod env, https://stackoverflow.com/questions/10181706/working-with-a-global-singleton-in-flask-wsgi-do-i-have-to-worry-about-race-c

logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)


@app.route('/')
def hello():
    return "Hello from Decode!"


@app.route('/init_onboarding', methods=['POST'])
def init_onboarding_request():
    """
    Endpoint called exclusively by the MRTD scanner to initialize a session

    :return: session id of newly created session
    :rtype: uuid4 string
    """
    # TODO: check who is requesting onboarding session, ip check/zenroom?
    # print("Not yet checked who is requesting onboarding session!")

    request_type = "onboarding"
    description = "I want to start onboarding session"

    new_session = session_manager.init_session(request_type, description)

    logging.info("New session was initialized [{}]".format(new_session['id']))
    logging.info("NEW SESSION: {}".format(new_session))

    return json_response({'session_id': new_session['id']})


@app.route("/attach_public_key", methods=['POST'])
def attach_public_key():
    """
    Endpoint called by client PWA in order to attach a public key to a session.
    Method will emit a status update to notify the MRTD scanner of this change.
    
    Request data must contain:
    - ['session_id']: Session ID of active session to attach public key to
    - ['public_key']: The public key

    :return: selected session
    :rtype: session dictionary
    """
    data = request.get_data()
    data_json = json.loads(data)
    session_id = data_json['session_id']
    public_key = data_json['public_key']

    data = {"public_key": public_key}

    session_status = "GOT_PUB_KEY"
    session = session_manager.append_session_data(session_id, data, session_status)

    logging.info("Public key was attached to session [{}]".format(session_id))
    
    return json_response({"response": session})


@app.route("/attach_encrypted_data", methods=['POST'])
def attach_encrypted_data():
    """
    Endpoint called by MRTD scanner exclusively to attach encrypted data to a session.
    Method will emit a status update to notify the client PWA of this change.

    Request data must contain:
    - ['session_id']: Session ID of active session to attach encrypted data to
    - ['encrypted_data']: The encrypted data

    :return: selected session
    :rtype: session dictionary
    """
    data = request.get_data()
    data_json = json.loads(data)
    session_id = data_json['session_id']
    encrypted_data = data_json['encrypted_data']

    data = {"encrypted": encrypted_data}
    session_status = "GOT_ENCR_DATA"
    session = session_manager.append_session_data(session_id, data, session_status)

    logging.info("Encrypted data was attached to session [{}]".format(session_id))

    return json_response({"response": session})


@app.route('/get_session', methods=['POST'])
def get_session():
    """
    Endpoint called for retrieving entire session, can be called by MRTD scanner and client PWA.

    Request data must contain:
    - ['session_id']: Session ID of session to be returned

    :return: selected session
    :rtype: session dictionary
    """
    data = request.get_data()
    data_json = json.loads(data)
    session_id = data_json['session_id']
    session = session_manager.get_session(session_id)

    if not session:
        logging.info("ACTIVE_SESSION:")
        logging.info(session_manager.active_sessions)

        msg = "No session to continue..."
        logging.error(msg)
        return json_response({'response': msg})

    if session['status'] == "GOT_ENCR_DATA":
        session = session_manager.change_status(session_id, "FINALIZED")

    logging.info("Returning session [{}]".format(session_id))

    return json_response({'response': session})


@app.route('/init_disclosure', methods=['POST'])
def init_disclosure_request():
    data = request.get_data()
    data_json = json.loads(data)
    attribute_request = data_json['attribute_request']
    description = data_json['description']
    new_session = session_manager.init_session(attribute_request, description)

    logging.info("New disclosure session was created [{}]".format(new_session['id']))

    return json_response({'session_id': new_session['id']})


@app.route('/get_session_status', methods=['POST'])
def get_session_status():
    data = request.get_data()
    data_json = json.loads(data)
    print("DATA_JSON:", data_json)
    session_id = data_json['session_id']

    # TODO: rename 'response' > 'status'
    with lock:
        response = session_manager.get_session_status(session_id)

    logging.info("Status [{0}] with id [{1}]".format(response, session_id))

    return json_response({'response': response})


@app.route('/accept_request', methods=['POST'])
def accept_request():
    data = request.get_data()
    data_json = json.loads(data)
    session_id = data_json['session_id']
    request_response = data_json['request_response']

    logging.info("Disclosure request accepted [{}]".format(session_id))
    status = 'FINALIZED'

    session = None
    if request_response == "VALID":
        random_color = "rgb({0},{1},{2})".format(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        # rand_color = RandomColor()
        # random_color = rand_color.generate()
        session = session_manager.append_session_data(session_id, {'request_status': request_response, 'secret': random_color}, status)

    elif request_response == "INVALID":
        session = session_manager.append_session_data(session_id, {'request_status': request_response}, status)
    
    return json_response({'response': session})

@app.route('/deny_request', methods=['POST'])
def deny_request():
    data = request.get_data()
    data_json = json.loads(data)
    session_id = data_json['session_id']

    logging.info("Disclosure request denied [{}]".format(session_id))

    status = 'FINALIZED'
    session = session_manager.append_session_data(session_id, {'request_status': 'DENIED'}, status)

    return json_response({'response': session})
    
@app.route('/get_active_sessions', methods=['GET'])
def get_active_sessions():
    return json_response(session_manager.active_sessions)


def json_response(data):
    response = Response(
        response=json.dumps(data),
        status=200,
        mimetype='application/json',
    )
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response


if __name__ == '__main__':
    logging.info("Server started")
    app.run(host='0.0.0.0', debug=True)
    # socketio.run(app, host='0.0.0.0', debug=False)
    logging.info("Server shutting down")
