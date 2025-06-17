# scripts/main.py

import os
import time
from camera_capture import capture_image
from inference import run_inference
from mqtt_handler import MQTTHandler
from logger_setup import setup_logger
from rabbit_handler import Rabbit
from configparser import ConfigParser
import json
import subprocess
from serial.tools import list_ports
from pydobotplus import Dobot
import logging
from mainDobot import plaats_blokje

subprocess.run(["python", "scripts/home.py"], check=True)

logger = setup_logger()

MODEL_PATH = os.path.abspath("model/rpi4-blokjes.eim")
IMAGE_PATH = os.path.abspath("images/captured_image.jpg")
SAVE_PATH = os.path.abspath("debug")

CONFIDENCE_THRESHOLD = 0.7

def see_if_all_block_labels_are_present(result, expected_labels):
    """
    Controleer of alle verwachte blokjeslabels aanwezig zijn in de detectie resultaten.
    """
    detected_labels = [box["label"] for box in result.get("boxes", [])]

    for label in expected_labels:
        if label not in detected_labels:
            logger.warning("Label '%s' niet gedetecteerd!", label)
            return False
    return True

class staticValues:
    dobot_device = None

def get_device():
    if staticValues.dobot_device:
        return staticValues.dobot_device
    
    available_ports = list_ports.comports()
    print(f'available ports: {[x.device for x in available_ports]}')
    port = available_ports[0].device
    device = Dobot(port=port)
    if not staticValues.dobot_device:
        staticValues.dobot_device = device
        


def handle_detection_trigger(payload):
    logger.info("trigger ontvangen: %s", payload)

    try:
        max_retries = 5
        retry_count = 0
        label = "onbekend"
        confidence = 0.0

        subprocess.run(["python", "scripts/blokje_oppak_camera.py"], check=True)

        while retry_count < max_retries:
            try:
                capture_image(IMAGE_PATH, camera_index=0)
                result = run_inference(MODEL_PATH, IMAGE_PATH, save_path=SAVE_PATH)
                logger.info("Inference resultaat: %s", result)

                label = result.get("highest_label", "onbekend")
                confidence = result.get("highest_confidence", 0.0)

                logger.info("Poging %d: %s (confidence: %.2f)", retry_count + 1, label, confidence)

                if confidence >= CONFIDENCE_THRESHOLD:
                    logger.info("Detectie boven drempel (%s, %.2f)", label, confidence)
                    break
                else:
                    logger.warning("Confidence te laag (%.2f), opnieuw proberen...", confidence)
                    retry_count += 1
                    time.sleep(1)

            except Exception as inner_error:
                logger.error("Fout tijdens poging %d: %s", retry_count + 1, inner_error)
                retry_count += 1
                time.sleep(1)

        if confidence < CONFIDENCE_THRESHOLD:
            logger.warning("Geen betrouwbare detectie na %d pogingen, label = 'onbekend'", max_retries)
            label = "onbekend"
            
        result2 = result.get("boxes", [])
        x_blok = None
        x_logo = None
        
        for box in result2:
            print(box)
            if box["label"].endswith("blokje"):
                if x_blok is None or box["value"] > x_blok["value"]:
                    x_blok = box
            elif box["label"].endswith("logo"):
                if x_logo is None or box["value"] > x_logo["value"]:
                    x_logo = box
        if x_blok:
            logger.info("Blokje gevonden: %s", x_blok)
        if x_logo:
            logger.info("Logo gevonden: %s", x_logo)
            
        result["boxes"] = [x_blok, x_logo] if x_blok or x_logo else []
        

        # Dobot aansturen op basis van label
        # normalized_label = (result["highest_label"] or "onbekend").strip().lower()

        plek1_labels = ["zwart blokje", "grijs logo"]
        plek2_labels = ["trigender blokje", "groen logo"]

        if see_if_all_block_labels_are_present(result, plek1_labels):
            plaats_blokje(get_device(), "plek1")
        elif see_if_all_block_labels_are_present(result, plek2_labels):
            plaats_blokje(get_device(), "plek2")
        else:
            plaats_blokje(get_device(), "onbekend")


            # subprocess.run(["python", "scripts/mainDobot.py", "--plaats", "plek1"], check=True)
            # subprocess.run(["python", "scripts/mainDobot.py", "--plaats", "plek2"], check=True)
            # subprocess.run(["python", "scripts/mainDobot.py", "--plaats", "onbekend"], check=True)


        
        if rabbitEnable:
            rabbit.publish("Detectie", f"band.{band_nummer}", json.dumps(result))
        else:
            mqtt.publish_detectie_resultaat(label)

    except Exception as outer_error:
        logger.critical("Fout in detectieproces: %s", outer_error)

if __name__ == "__main__":
    config = ConfigParser()
    config.read("config/config.ini")
    mqtt = MQTTHandler(config_path="config/config.ini", on_trigger=handle_detection_trigger, logger=logger)
    rabbit = Rabbit(config_path="config/config.ini", on_trigger=handle_detection_trigger, logger=logger)
    rabbitEnable = config.get("RABBITMQ", "enabled", fallback="false").lower() == "true"
    band_nummer = config.getint("RABBITMQ", "band_nummer", fallback=10)
    if(rabbitEnable):
        rabbit.setup()
        qu = f"Detectie_resultaat_band_{band_nummer}"
        rabbit.declare_exchange("Detectie")
        rabbit.declare_queue(qu)
        rabbit.bind_queue(qu, "Detectie", routing_key=f"band.{band_nummer}")
        rabbit.loop()
        logger.info("RabbitMQ gestart. Wacht op berichten...")
    else:
        mqtt.start()
    logger.info("Systeem gestart. Wacht op MQTT-trigger...")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Programma afgesloten door gebruiker.")
