import os, json, urllib.request, urllib.parse

DEFAULT_CITY = os.getenv("CITY", "Cairo")

def get_weather(city=None):
    city = city or DEFAULT_CITY
    try:
        url = f"https://wttr.in/{urllib.parse.quote(city)}?format=j1"
        with urllib.request.urlopen(url, timeout=5) as r:
            data = json.loads(r.read())
        cur  = data["current_condition"][0]
        desc = cur["weatherDesc"][0]["value"]
        temp = cur["temp_C"]
        feel = cur["FeelsLikeC"]
        hum  = cur["humidity"]
        return (f"Currently {desc} in {city.title()}, Sir. "
                f"{temp}°C, feels like {feel}°C, humidity {hum}%.")
    except Exception as e:
        return f"I couldn't retrieve the weather right now, Sir. ({e})"