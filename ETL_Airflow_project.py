#Importing the necessary libraries
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import timedelta, datetime
from sqlalchemy import create_engine
import requests as re
import pandas as pd

#Defining default arguments for the DAG
default_args = {
    'owner': 'Michael',
    'retries': 1,
    'start_date': datetime(2023,9,20,14,7),
    'retry_delay': timedelta(minutes=1)
}

# Function to fetch data from the API
def get_api_data(url):
    try:
        response = re.get(url)
        response.raise_for_status()
        data = response.json()
        return data
    except Exception as e:
        raise Exception(f"Error fetching data from API: {str(e)}")

# Function to extract data from the API
def extract_data(data):
    first_name = []
    last_name  = []
    gender  = []
    email  = []
    dob  = []
    country  = []
    street_name  = []
    city  = []
    state  = []
    postcode  = []
    phone  = []
    mobile  = []

    for item in data['results']:
        first_name.append(item['name']['first'])
        last_name.append(item['name']['last'])
        gender.append(item['gender'])
        email.append(item['email'])
        dob_string = item['dob']['date']
        dob_object = datetime.strptime(dob_string, '%Y-%m-%dT%H:%M:%S.%fZ')
        dob_formatted = dob_object.strftime('%Y-%m-%d')
        dob.append(dob_formatted)
        country.append(item['location']['country'])
        street_address = item['location']['street']
        street_name = f"{street_address['number']} {street_address['name']}"
        city.append(item['location']['city'])
        state.append(item['location']['state'])
        postcode.append(item['location']['postcode'])
        phone.append(item['phone'])
        mobile.append(item['cell'])
        
    return first_name, last_name, gender, email, dob, country, street_name, city, state, postcode, phone, mobile

# Function to create dataframe
def create_data_frame(data, street_name):
    user_data = []

    for item in data:
        user_info = {
            'first_name': item['first_name'] if 'first_name' in item else None,
            'last_name': item['last_name'] if 'last_name' in item else None,
            'gender': item['gender'] if 'gender' in item else None,
            'email': item['email'] if 'email' in item else None,
            'dob': item['dob'] if 'dob' in item else None,
            'country': item['country'] if 'country' in item else None,
            'street_address' : street_name if 'street_address' in item else None,
            'city': item['city'] if 'city' in item else None,
            'state': item['state'] if 'state' in item else None,
            'postcode': item['postcode'] if 'postcode' in item else None,
            'phone': item['phone'] if 'phone' in item else None,
            'mobile': item['mobile'] if 'mobile' in item else None  
        }
        user_data.append(user_info)

    user_df = pd.DataFrame(user_data)
    return user_df

# Function to load data to PostgreSQL
def load_data(user_df,table_name,connection):
    user_df.to_sql('user_data', engine, if_exists = 'append')

# Function to run the API processing workflow
def run_api_processing(url, engine, **kwargs):
    
    # Fetch Data
    api_data = get_api_data(url)
    
    # Extract Data
    first_name, last_name, gender, email, dob, country, street_name, city, state, postcode, phone, mobile = extract_data(api_data)
    
    # Create DataFrame
    user_df = create_data_frame(api_data, street_name)
    
    # Load Data
    load_data(user_df, 'user_data', engine)    

# Variables for api and database connection
url = 'https://randomuser.me/api/'
engine = create_engine('postgresql://postgres:kisan@localhost:5432/c5')

# Creating DAG
with DAG(
    dag_id = 'api_etl_process',
    description = 'Designing and implementing an ETL pipeline using Apache Airflow',
    schedule_interval = '@daily',
    default_args = default_args,
    catchup = False,
    doc_md = 'Extracting data from an API, performing a data transformations, loading the data into a PostgreSQL database'

) as dag:

        task_id = 'api_etl_process_task'
        upload_task = PythonOperator(
            task_id = task_id,
            python_callable = run_api_processing,
            op_kwargs={'url': url, 'engine': engine}
        )