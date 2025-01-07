import os
import json
import boto3
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class WeatherDashboard:
    def __init__(self):
        self.api_key = os.getenv('OPENWEATHER_API_KEY')
        self.bucket_name = os.getenv('AWS_BUCKET_NAME')
        self.s3_client = boto3.client('s3')
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table('WeatherForecasts')

    def fetch_weather(self, city):
        """Fetch current weather data from OpenWeather API"""
        base_url = "http://api.openweathermap.org/data/2.5/weather"
        params = {
            "q": city,
            "appid": self.api_key,
            "units": "imperial"
        }
        
        try:
            response = requests.get(base_url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching weather data: {e}")
            return None

    def fetch_forecast(self, city):
        """Fetch 5-day weather forecast from OpenWeather API"""
        base_url = "http://api.openweathermap.org/data/2.5/forecast"
        params = {
            "q": city,
            "appid": self.api_key,
            "units": "imperial"
        }
        
        try:
            response = requests.get(base_url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching forecast data: {e}")
            return None

    def save_to_s3(self, weather_data, city):
        """Save weather data to S3 bucket"""
        if not weather_data:
            return False
            
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        file_name = f"weather-data/{city}/{timestamp}.json"
        
        try:
            weather_data['timestamp'] = timestamp
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=file_name,
                Body=json.dumps(weather_data),
                ContentType='application/json'
            )
            print(f"Successfully saved data for {city} to S3")
            return True
        except Exception as e:
            print(f"Error saving to S3: {e}")
            return False

    def save_forecast_to_dynamodb(self, forecast_data, city):
        """Save forecast data to DynamoDB"""
        if not forecast_data:
            return False

        try:
            for forecast in forecast_data['list']:
                item = {
                    'CityDate': f"{city}#{forecast['dt']}",
                    'City': city,
                    'Timestamp': forecast['dt'],
                    'Temperature': forecast['main']['temp'],
                    'FeelsLike': forecast['main']['feels_like'],
                    'Humidity': forecast['main']['humidity'],
                    'Description': forecast['weather'][0]['description']
                }
                self.table.put_item(Item=item)
            print(f"Successfully saved forecast for {city} to DynamoDB")
            return True
        except Exception as e:
            print(f"Error saving to DynamoDB: {e}")
            return False

def main():
    dashboard = WeatherDashboard()
    
    cities = ["Philadelphia", "Seattle", "New York"]
    
    for city in cities:
        print(f"\nFetching current weather for {city}...")
        weather_data = dashboard.fetch_weather(city)
        if weather_data:
            temp = weather_data['main']['temp']
            feels_like = weather_data['main']['feels_like']
            humidity = weather_data['main']['humidity']
            description = weather_data['weather'][0]['description']
            
            print(f"Current Temperature: {temp}°F")
            print(f"Feels like: {feels_like}°F")
            print(f"Humidity: {humidity}%")
            print(f"Conditions: {description}")
            
            # Save current weather to S3
            success = dashboard.save_to_s3(weather_data, city)
            if success:
                print(f"Current weather data for {city} saved to S3!")

        print(f"\nFetching 5-day forecast for {city}...")
        forecast_data = dashboard.fetch_forecast(city)
        if forecast_data:
            # Save forecast to DynamoDB
            success = dashboard.save_forecast_to_dynamodb(forecast_data, city)
            if success:
                print(f"Forecast data for {city} saved to DynamoDB!")

            # Display forecast summary
            for forecast in forecast_data['list'][:5]:  # Display next 5 forecasts
                date = datetime.fromtimestamp(forecast['dt'])
                temp = forecast['main']['temp']
                description = forecast['weather'][0]['description']
                print(f"{date.strftime('%Y-%m-%d %H:%M')}: {temp}°F, {description}")
        else:
            print(f"Failed to fetch forecast data for {city}")

if __name__ == "__main__":
    main()
