import os
import json
import boto3
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dotenv import load_dotenv
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
import matplotlib.pyplot as plt

# Load environment variables
load_dotenv()

class WeatherDashboard:
    def __init__(self):
        self.api_key = os.getenv('OPENWEATHER_API_KEY')
        self.bucket_name = os.getenv('AWS_BUCKET_NAME')
        self.s3_client = boto3.client('s3')
        self.athena_client = boto3.client('athena')
        self.glue_client = boto3.client('glue')

    def create_bucket_if_not_exists(self):
        """Create S3 bucket if it doesn't exist"""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            print(f"Bucket {self.bucket_name} exists")
        except:
            print(f"Creating bucket {self.bucket_name}")
        try:
            self.s3_client.create_bucket(Bucket=self.bucket_name)
            print(f"Successfully created bucket {self.bucket_name}")
        except Exception as e:
            print(f"Error creating bucket: {e}")

    def fetch_weather(self, city):
        """Fetch weather data from OpenWeather API"""
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

    def create_glue_crawler(self):
        """Create AWS Glue Crawler to catalog S3 data"""
        try:
            self.glue_client.create_crawler(
                Name='WeatherDataCrawler',
                Role='AWSGlueServiceRole',
                DatabaseName='weather_database',
                Targets={
                    'S3Targets': [
                        {'Path': f's3://{self.bucket_name}/weather-data/'}
                    ]
                },
                Schedule='cron(0 1 * * ? *)'
            )
            print("Successfully created Glue Crawler")
        except Exception as e:
            print(f"Error creating Glue Crawler: {e}")

    def run_athena_query(self, query):
        """Run Athena query on the weather data"""
        try:
            response = self.athena_client.start_query_execution(
                QueryString=query,
                QueryExecutionContext={
                    'Database': 'weather_database'
                },
                ResultConfiguration={
                    'OutputLocation': f's3://{self.bucket_name}/athena-results/'
                }
            )
            return response['QueryExecutionId']
        except Exception as e:
            print(f"Error running Athena query: {e}")
            return None

    def fetch_historical_data(self, city, days=30):
        """Fetch historical weather data for the past 30 days"""
        base_url = "http://api.openweathermap.org/data/2.5/onecall/timemachine"
        historical_data = []
        
        for i in range(days):
            dt = int((datetime.now() - timedelta(days=i)).timestamp())
            params = {
                "lat": 40.7128,  # Example: New York latitude
                "lon": -74.0060,  # Example: New York longitude
                "dt": dt,
                "appid": self.api_key,
                "units": "imperial"
            }
            
            try:
                response = requests.get(base_url, params=params)
                response.raise_for_status()
                data = response.json()
                historical_data.append(data)
            except requests.exceptions.RequestException as e:
                print(f"Error fetching historical data: {e}")
        
        return historical_data

    def train_weather_model(self, historical_data):
        """Train a machine learning model on historical weather data"""
        df = pd.DataFrame(historical_data)
        
        features = ['temp', 'humidity', 'wind_speed']
        target = 'feels_like'
        
        X = df[features]
        y = df[target]
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)
        
        y_pred = model.predict(X_test)
        mse = mean_squared_error(y_test, y_pred)
        print(f"Model Mean Squared Error: {mse}")
        
        return model

    def visualize_weather_trends(self, historical_data):
        """Visualize weather trends over time"""
        df = pd.DataFrame(historical_data)
        df['date'] = pd.to_datetime(df['dt'], unit='s')
        
        plt.figure(figsize=(12, 6))
        plt.plot(df['date'], df['temp'], label='Temperature')
        plt.plot(df['date'], df['humidity'], label='Humidity')
        plt.xlabel('Date')
        plt.ylabel('Value')
        plt.title('Weather Trends')
        plt.legend()
        plt.savefig('weather_trends.png')
        plt.close()

def main():
    dashboard = WeatherDashboard()
    
    # Create bucket if needed
    dashboard.create_bucket_if_not_exists()
    
    # Create Glue Crawler
    dashboard.create_glue_crawler()
    
    cities = ["Philadelphia", "Seattle", "New York"]
    
    for city in cities:
        print(f"\nFetching weather for {city}...")
        weather_data = dashboard.fetch_weather(city)
        if weather_data:
            temp = weather_data['main']['temp']
            feels_like = weather_data['main']['feels_like']
            humidity = weather_data['main']['humidity']
            description = weather_data['weather'][0]['description']
            
            print(f"Temperature: {temp}°F")
            print(f"Feels like: {feels_like}°F")
            print(f"Humidity: {humidity}%")
            print(f"Conditions: {description}")
            
            # Save to S3
            success = dashboard.save_to_s3(weather_data, city)
            if success:
                print(f"Weather data for {city} saved to S3!")
        else:
            print(f"Failed to fetch weather data for {city}")

    #
