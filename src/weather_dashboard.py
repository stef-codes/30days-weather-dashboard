import os
import json
import boto3
import requests
from decimal import Decimal
from datetime import datetime, timedelta
from dotenv import load_dotenv
from botocore.exceptions import ClientError

# Load environment variables
load_dotenv()

class WeatherDashboard:
    def __init__(self):
        self.api_key = os.getenv('OPENWEATHER_API_KEY')
        self.bucket_name = os.getenv('AWS_BUCKET_NAME')
        self.s3_client = boto3.client('s3')
        self.dynamodb = boto3.resource('dynamodb')
        self.table_name = 'WeatherForecasts'
        self.table = self.create_dynamo_table()

    def create_dynamo_table(self):
        """Create DynamoDB table if it doesn't exist"""
        try:
            table = self.dynamodb.create_table(
                TableName=self.table_name,
                KeySchema=[
                    {
                        'AttributeName': 'CityDate',
                        'KeyType': 'HASH'
                    }
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': 'CityDate',
                        'AttributeType': 'S'
                    }
                ],
                ProvisionedThroughput={
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            )
            table.meta.client.get_waiter('table_exists').wait(TableName=self.table_name)
            print(f"Table {self.table_name} created successfully.")
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceInUseException':
                print(f"Table {self.table_name} already exists.")
                table = self.dynamodb.Table(self.table_name)
            else:
                print(f"Unexpected error: {e}")
                raise
        return table

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
            with self.table.batch_writer() as batch:
                for forecast in forecast_data['list']:
                    item = {
                        'CityDate': f"{city}#{forecast['dt']}",
                        'City': city,
                        'Timestamp': forecast['dt'],
                        'Temperature': Decimal(str(forecast['main']['temp'])),
                        'FeelsLike': Decimal(str(forecast['main']['feels_like'])),
                        'Humidity': Decimal(str(forecast['main']['humidity'])),
                        'Description': forecast['weather'][0]['description']
                    }
                    batch.put_item(Item=item)
            print(f"Successfully saved forecast for {city} to DynamoDB")
            return True
        except Exception as e:
            print(f"Error saving to DynamoDB: {e}")
            return False

    def get_daily_forecasts(self, forecast_data):
        """Extract one forecast per day for the next 5 days"""
        daily_forecasts = []
        current_date = datetime.now().date()
        for forecast in forecast_data['list']:
            forecast_date = datetime.fromtimestamp(forecast['dt']).date()
            if forecast_date > current_date and len(daily_forecasts) < 5:
                if not daily_forecasts or forecast_date > daily_forecasts[-1]['date']:
                    daily_forecasts.append({
                        'date': forecast_date,
                        'temp': forecast['main']['temp'],
                        'feels_like': forecast['main']['feels_like'],
                        'humidity': forecast['main']['humidity'],
                        'description': forecast['weather'][0]['description']
                    })
        return daily_forecasts

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
            daily_forecasts = dashboard.get_daily_forecasts(forecast_data)
            print(f"\n5-day forecast for {city}:")
            for forecast in daily_forecasts:
                print(f"{forecast['date'].strftime('%Y-%m-%d')}: {forecast['temp']}°F, {forecast['description']}")
        else:
            print(f"Failed to fetch forecast data for {city}")

if __name__ == "__main__":
    main()
