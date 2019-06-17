#!/usr/bin/env python

import os
import time
import fileinput
import json
import paho.mqtt.client as mqtt

MQTT_HOST = os.environ.get("MQTT_HOST", None)
MQTT_PORT = os.environ.get("MQTT_PORT", 1883)

channel_maps = {
    "temperature_C": ("Temperature", "float", "°C"),
    "temperature_F": ("Temperature", "float", "°F"),
    "maybe_battery": ("Battery Level", "integer", "%"),
    "battery_ok": ("Battery OK", "boolean", ""),
    "humidity": ("Humidity", "integer", "%"),
    "moisture": ("Moisture", "integer","%"),
    "pressure_kPa": ("Pressure", "float", "kPa"),
    "pressure_hPa": ("Pressure", "float", "hPa"),

    "wind_speed_km_h": ("Wind Speed", "float", "km/h"),
    "wind_speed_m_s": ("Wind Speed", "float", "m/s"),

    "gust_speed_km_h": ("Gust Speed", "float", "km/h"),
    "gust_speed_m_s": ("Gust Speed", "float", "m/s"),

    "wind_dir_deg": ("Wind Direction", "integer", "°"),

    "rain_mm": ("Rain Total", "float", "mm"),
    "rain_mm_h": ("Rain Rate", "float", "mm/h"),

    "depth_cm": ("Depth", "float", "cm"),

    # TODO: Handle this mess better
    "switch1": ("Switch 1", "boolean", ""),
    "switch2": ("Switch 2", "boolean", ""),
    "switch3": ("Switch 3", "boolean", ""),
    "switch4": ("Switch 4", "boolean", ""),
    "switch5": ("Switch 5", "boolean", ""),

    "flags": ("Flags", "string", ""),
    "state": ("State", "string", ""),
    "status": ("Status", "string", ""),
    "subtype": ("Subtype", "string", ""),
    "code": ("Code", "string", ""),
    "unit": ("Unit", "integer", ""),
    "learn": ("Learn", "boolean", ""),
}

boolean_map = {
    "0": "false",
    "1": "true",
    "CLOSED": "false",
    "OPEN": "true",
    "No": "false",
    "Yes": "true",
}

def send_message(mqttc, topic, value, retain=False):
    #print("%s: %s" % (topic, str(value)))
    mqttc.publish(topic, str(value), qos=1, retain=retain)


def sanitize(text):
    return (text
            .replace(" ", "_")
            .replace("/", "_")
            .replace(".", "_")
            .replace("&", ""))

def mqtt_connect(client, userdata, flags, rc):
    """Log MQTT connects."""
    #print("MQTT connected: " + mqtt.connack_string(rc))
    pass


def mqtt_disconnect(client, userdata, rc):
    """Log MQTT disconnects."""
    #print("MQTT disconnected: " + mqtt.connack_string(rc))
    pass

def get_device_id(data):
    dev_id = "rtl433_" + str(data["protocol"])
    if "channel" in data:
        dev_id += "_" + str(data["channel"])
    dev_id += "_" + str(data["id"])
    return dev_id

def get_client():
    mqttc = mqtt.Client()
    mqttc.on_connect = mqtt_connect
    mqttc.on_disconnect = mqtt_disconnect
    mqttc.connect_async(MQTT_HOST, MQTT_PORT, 60)
    mqttc.loop_start()
    return mqttc

def setup_device(data, base_topic):
    mqttc = get_client()
    name = data["model"]

    if "type" in data:
        name += " " + data["type"]

    mqttc.will_set(base_topic + "$state", "lost", qos=2, retain=True)
    send_message(mqttc, base_topic + "$state", "init", True)
    send_message(mqttc, base_topic + "$homie", "3.0", True)
    send_message(mqttc, base_topic + "$name", name, True)
    send_message(mqttc, base_topic + "$implementation", "rtl433-to-homie", True)
    send_message(mqttc, base_topic + "$nodes", "sensor", True)

    props = []

    sensor_topic = base_topic + "sensor/"
    send_message(mqttc, sensor_topic + "$name", name, True)
    send_message(mqttc, sensor_topic + "$type", "Sensor", True)

    for key, value in data.items():
        if key in channel_maps:
            tup = channel_maps[key]
            key_topic = key.replace("_", "-")
            props.append(key_topic)
            send_message(mqttc, sensor_topic + key_topic + "/$name", tup[0], True)
            send_message(mqttc, sensor_topic + key_topic + "/$datatype", tup[1], True)
            if tup[2] != "":
                send_message(mqttc, sensor_topic + key_topic + "/$unit", tup[2], True)
            send_message(mqttc, sensor_topic + key_topic + "/$settable", "false", True)

    send_message(mqttc, sensor_topic + "$properties", ",".join(props), True)
    send_message(mqttc, base_topic + "$state", "ready", True)
    
    return mqttc


cached_items = { }

def rtl_433_probe():


    for line in fileinput.input():
        try:
            data = json.loads(line)

            dev_id = get_device_id(data)
            dev_id = dev_id.replace("_", "-")

            base_topic = "homie/" + dev_id + "/"

            if dev_id not in cached_items:
                cached_items[dev_id] = setup_device(data, base_topic)

            mqttc = cached_items[dev_id]

            send_message(mqttc, base_topic + "$state", "ready", True)

            sensor_topic = base_topic + "sensor/"

            for key, value in data.items():
                if key in channel_maps:
                    tup = channel_maps[key]
                    if tup[1] == "boolean":
                        value = boolean_map[str(value)]
                    send_message(mqttc, sensor_topic + key.replace("_", "-"), value)

            send_message(mqttc, base_topic + "$state", "sleeping", True)
            print(line)

        except ValueError:
            print ("ERROR: " + line)
            

if __name__ == "__main__":
    rtl_433_probe()
    for key, value in cached_items.items():
        value.disconnect()