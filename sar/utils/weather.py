import requests, json

import logging
logger = logging.getLogger("nosar.sar.utils.weather")

def getCurrentWeather():
    ret_val = "the weather today"
    try:
        # Enter your API key here
        api_key = "db52fb8fd45305e3811553befb009d67"
        base_url = "http://api.openweathermap.org/data/2.5/weather?"
        city_name = "Delft"
        complete_url = base_url + "appid=" + api_key + "&q=" + city_name
        response = requests.get(complete_url)
        x = response.json()
        # Now x contains list of nested dictionaries
        # Check the value of "cod" key is equal to
        # "404", means city is found otherwise,
        # city is not found
        if x["cod"] != "404":
            # store the value of "main"
            # key in variable y
            y = x["main"]
            current_temperature = int(round(float(y["temp"])-273.15,0))
            # current_pressure = y["pressure"]
            current_humidity = float(y["humidity"])
            if current_humidity > 60:
                current_humidity = "high"
            elif current_humidity < 40:
                current_humidity = "low"
            else:
                current_humidity = "decent"
            z = x["weather"]
            weather_description = z[0]["description"]

            ret_val = "Today is "+str(current_temperature)+" degrees Celsius, with a "+str(current_humidity)+" humidity. We have "+str(weather_description)+"."
    except:
        ret_val = "the weather today"

    return ret_val
