import json
from datetime import datetime

import werkzeug.exceptions
from flask import Blueprint, jsonify, Response
from flask import current_app as app

from .constants import CFG_MQTT_TOPIC_POWER_CONTROL, CFG_MQTT_TOPIC_POWER_STATUS
from .data import Data
from .util import Util

utilities = Util(app)
data = Data()
bp = Blueprint('routes', __name__)


@utilities.mqtt.on_connect()
def handle_connect(client, userdata, flags, rc):
    utilities.mqtt.subscribe(utilities.config[CFG_MQTT_TOPIC_POWER_STATUS])


@utilities.mqtt.on_message()
def handle_message(client, userdata, message):
    payload = json.loads(message.payload.decode())
    data.devices[payload['deviceName']] = payload['status']


@bp.get('/power-status/<device_name>')
def get_power_status(device_name) -> Response:
    app.logger.debug(f'GET /power-status/{device_name} called')

    status = data.devices.get(device_name, 'unknown')
    response = {'status': f'{status}'}
    app.logger.debug(f'Reported status for {device_name}: {status}')

    return jsonify(response)


@bp.post('/power-control/<device_name>/on')
def post_power_control_on(device_name) -> Response:
    app.logger.debug(f'POST /power-control/{device_name}/on called')

    now = datetime.now()
    control_request = data.power_control_requests.get(device_name, None)
    if not control_request or (now - control_request).total_seconds() > 30:
        utilities.mqtt.publish(utilities.config[CFG_MQTT_TOPIC_POWER_CONTROL], f'{{"deviceName": "{device_name}", "action": "powerOn"}}'.encode())
        data.power_control_requests[device_name] = now

    return Response(status=204)


@bp.post('/power-control/<device_name>/off')
def post_power_control_off(device_name) -> Response:
    app.logger.debug(f'POST /power-control/{device_name}/off called')

    now = datetime.now()
    control_request = data.power_control_requests.get(device_name, None)
    if not control_request or (now - control_request).total_seconds() > 30:
        utilities.mqtt.publish(utilities.config[CFG_MQTT_TOPIC_POWER_CONTROL], f'{{"deviceName": "{device_name}", "action": "powerOff"}}'.encode())
        data.power_control_requests[device_name] = now

    return Response(status=204)


@bp.errorhandler(werkzeug.exceptions.HTTPException)
def handle_bad_request(error) -> Response:
    app.logger.debug(f'Handling error {error}')
    response = jsonify({'message': error.description})
    response.status_code = error.code
    return response


@bp.get('/health')
def get_health() -> Response:
    return Response(status=204)
