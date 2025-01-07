


# 30 Day Weather Dashboard

The **30 Day Weather Dashboard** is a Python-based weather application that provides real-time weather data and 5-day forecasts. It uses the OpenWeather API to fetch weather information and integrates with AWS services like S3 and DynamoDB for data storage.

## Features

- Fetch **current weather** data for multiple cities.
- Retrieve **5-day forecasts** with daily summaries.
- Save weather data to **AWS S3**.
- Store detailed forecasts in **AWS DynamoDB** for analysis.
- Automatically create the required DynamoDB table if it doesn't exist.
- Efficient batch processing for storing forecast data in DynamoDB.

## Tech Stack

- **Programming Language**: Python
- **APIs**: OpenWeather API for weather and forecast data
- **Cloud Services**:
  - **AWS S3** for storage
  - **AWS DynamoDB** for database management
- **Libraries**:
  - `boto3`: AWS SDK for Python
  - `requests`: To interact with the OpenWeather API
  - `dotenv`: To manage environment variables

## Prerequisites

Before running the application, ensure you have the following:

1. **Python 3.8 or later** installed.
2. An **OpenWeather API key**. Sign up at [OpenWeather](https://openweathermap.org/api) to get your key.
3. An **AWS account** with permissions to use S3 and DynamoDB services.

## Installation

Follow these steps to set up the project:

### Step 1: Clone the Repository
```bash
git clone https://github.com/stef-codes/30days-weather-dashboard.git
cd 30days-weather-dashboard
```

### Step 2: Create a Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Set Up Environment Variables
Create a `.env` file in the project root and add the following:

```env
OPENWEATHER_API_KEY=your_openweather_api_key
AWS_BUCKET_NAME=your_aws_bucket_name
AWS_ACCESS_KEY_ID=your_aws_access_key_id
AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key
AWS_REGION=your_aws_region
```

Replace the placeholder values (`your_openweather_api_key`, etc.) with your actual credentials.

### Step 5: Run the Application
Run the application with the following command:

```bash
python weather_dashboard.py
```

## Usage

1. Open the `main()` function in the `weather_dashboard.py` file.
2. Update the `cities` list with the cities for which you want weather data.
3. Run the script to:
   - Fetch current weather and display it in the console.
   - Save weather data to your AWS S3 bucket.
   - Store 5-day forecast data in your AWS DynamoDB table.

## Example Output

Below is a sample output when the script is run:

```plaintext
Fetching current weather for Philadelphia...
Current Temperature: 75°F
Feels like: 73°F
Humidity: 65%
Conditions: clear sky

Fetching 5-day forecast for Philadelphia...
Successfully saved forecast for Philadelphia to DynamoDB!

5-day forecast for Philadelphia:
2024-01-01: 70°F, scattered clouds
2024-01-02: 72°F, clear sky
2024-01-03: 68°F, light rain
2024-01-04: 65°F, overcast clouds
2024-01-05: 67°F, moderate rain
```

## Roadmap

- [ ] Add data visualization in a web dashboard.
- [ ] Include air quality and UV index metrics.
- [ ] Schedule automated data fetching and storage tasks.
- [ ] Add support for other weather APIs.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.

---

## Contributing

Contributions are welcome! If you'd like to add new features or fix bugs, please fork the repository and create a pull request.
