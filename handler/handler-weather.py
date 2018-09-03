# encoding: utf-8
from __future__ import unicode_literals

import datetime
import json

import paho.mqtt.client as mqtt
import requests

fromtimestamp = datetime.datetime.fromtimestamp

# MQTT client to connect to the bus
mqtt_client = mqtt.Client()
HOST = "localhost"
PORT = 1883
WEATHER_TOPICS = ['hermes/intent/searchWeatherForecastTemperature',
                  'hermes/intent/searchWeatherForecastCondition',
                  'hermes/intent/searchWeatherForecast']

# WEATHER API
WEATHER_API_BASE_URL = "http://api.openweathermap.org/data/2.5"
WEATHER_API_KEY = "<YOUR_KEY>"
DEFAULT_CITY_NAME = "Paris"
UNITS = "metric" 



# Subscribe to the important messages
def on_connect(client, userdata, flags, rc):
    for topic in WEATHER_TOPICS:
        mqtt_client.subscribe(topic)


# Process a message as it arrives
def on_message(client, userdata, msg):
    print msg.topic

    if msg.topic not in WEATHER_TOPICS:
        return

    slots = parse_slots(msg)
    weather_forecast = get_weather_forecast(slots)


    if msg.topic == 'hermes/intent/searchWeatherForecast':
        '''
        Complete answer: 
            - condition
            - current temperature
            - max and min temperature
            - warning about rain or snow if needed
        ''' 
        response = ("It will be mostly {0}{1} today. "
                    "Current temperature is {2} degrees. " 
                    "Max temperature will be {3}. "
                    "Minimum will be {4}.").format(
            weather_forecast["mainCondition"], 
            weather_forecast["inLocation"],
            weather_forecast["temperature"], 
            weather_forecast["temperatureMax"], 
            weather_forecast["temperatureMin"]
        )
        response = add_warning_if_needed(response, weather_forecast)
    
    elif msg.topic == 'hermes/intent/searchWeatherForecastCondition':
        '''
        Condition-focused answer: 
            - condition
            - warning about rain or snow if needed
        ''' 
        response = "It will be mostly {0}{1} today.".format(
            weather_forecast["mainCondition"], 
            weather_forecast["inLocation"]
        )
        response = add_warning_if_needed(response, weather_forecast)
    
    elif msg.topic == 'hermes/intent/searchWeatherForecastTemperature':
        '''
        Temperature-focused answer: 
            - current temperature
            - max and min temperature
        ''' 
        response = ("Current temperature{0} is {1} degrees. "
                    "Today, max temperature will be {2}. "
                    "Minimum will be {3}.").format(
            weather_forecast["inLocation"],
            weather_forecast["temperature"], 
            weather_forecast["temperatureMax"], 
            weather_forecast["temperatureMin"]
        )
    
    session_id = parse_session_id(msg)
    say(session_id, response)


def parse_slots(msg):
    '''
    We extract the slots as a dict
    '''
    data = json.loads(msg.payload)
    return {slot['slotName']: slot['rawValue'] for slot in data['slots']}


def parse_session_id(msg): 
    '''
    Extract the session id from the message
    '''
    data = json.loads(msg.payload)
    return data['sessionId']
  
  
def say(session_id, text):
    '''
    Print the output to the console and to the TTS engine
    '''
    print(text)
    mqtt_client.publish('hermes/dialogueManager/endSession', json.dumps({'text': text, "sessionId" : session_id}))


def parse_open_weather_map_forecast_response(response, location):
    '''
    Parse the output of Open Weather Map's forecast endpoint
    '''
    today = fromtimestamp(response["list"][0]["dt"]).day
    today_forecasts = filter(lambda forecast: fromtimestamp(forecast["dt"]).day==today, response["list"])
    
    all_min = [x["main"]["temp_min"] for x in today_forecasts]
    all_max = [x["main"]["temp_max"] for x in today_forecasts]
    all_conditions = [x["weather"][0]["main"] for x in today_forecasts]
    rain = filter(lambda forecast: forecast["weather"][0]["main"] == "Rain", today_forecasts)
    snow = filter(lambda forecast: forecast["weather"][0]["main"] == "Snow", today_forecasts)

    return {
        "location": location,
        "inLocation": " in {0}".format(location) if location else "",         
        "temperature": int(today_forecasts[0]["main"]["temp"]),
        "temperatureMin": int(min(all_min)),
        "temperatureMax": int(max(all_max)),
        "rain": len(rain) > 0,
        "snow": len(snow) > 0,
        "mainCondition": max(set(all_conditions), key=all_conditions.count).lower()
    }


def get_weather_forecast(slots):
    '''
    Parse the query slots, and fetch the weather forecast from Open Weather Map's API
    '''
    location = slots.get("forecast_locality", None) \
            or slots.get("forecast_country", None)  \
            or slots.get("forecast_region", None)  \
            or slots.get("forecast_geographical_poi", None) \
            or DEFAULT_CITY_NAME
    forecast_url = "{0}/forecast?q={1}&APPID={2}&units={3}".format(
        WEATHER_API_BASE_URL, location, WEATHER_API_KEY, UNITS)
    r_forecast = requests.get(forecast_url)
    return parse_open_weather_map_forecast_response(r_forecast.json(), location)


def add_warning_if_needed(response, weather_forecast):
    if weather_forecast["rain"] and weather_forecast["mainCondition"] != "rain":
        response += ' Be careful, it may rain.'
    if weather_forecast["snow"] and weather_forecast["mainCondition"] != "snow":
        response += ' Be careful, it may snow.'
    return response


if __name__ == '__main__':
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    mqtt_client.connect(HOST, PORT)
    mqtt_client.loop_forever()

