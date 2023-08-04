from flask import Flask, Config
from flask_mqtt import Mqtt

from .constants import CFG_LOG_LEVEL


class Util:
    config: Config
    mqtt: Mqtt

    def __init__(self, app: Flask):
        self.config = app.config
        self.mqtt = Mqtt()
        self.mqtt.init_app(app)

        app.logger.setLevel(self.config[CFG_LOG_LEVEL])
        app.logger.info('Initializing REST interface for MAAS webhook for MQTT power control')
        app.logger.info(f'Log level set to {self.config[CFG_LOG_LEVEL]}')

        app.logger.info('Ready to accept requests')
