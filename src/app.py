#!/usr/bin/python3
import asyncio
import json
import websockets
import logging
import cachetools
import hass_ae.client as hac
import hass_ae.config
import hass_ae.components
import hass_ae

import automation

logger = logging.getLogger(__name__)

def configure_logging(log_level, ws_log_level):
    logging.basicConfig(
        format="%(asctime)s %(levelname)s:%(name)s: %(message)s",
        level=log_level,
        datefmt="%H:%M:%S"
    )
    logging.getLogger('websockets.protocol').level = ws_log_level
    logging.getLogger('websockets.client').level = ws_log_level

def run():
    config = hass_ae.config.Config()

    configure_logging(
        logging.getLevelName(config['log_level'].upper()),
        logging.getLevelName(config['ws_log_level'].upper())
     ) 

    hass_ae.run(config, automation.setup)

if __name__ == '__main__':
    run()