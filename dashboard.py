from flask import Flask, render_template
import pandas as pd
import matplotlib.pyplot as plt
import sqlite3
from io import BytesIO
import base64
import logging

app = Flask(__name__)
app.debug = True  # Enable debug mode

# Configure logging
logging.basicConfig(filename='dashboard.log', level=logging.DEBUG, format='%(asctime)s:%(levelname)s:%(message)s')

def get_db_connection():
    conn = sqlite3.connect('ppc_bot.db')
    return conn

def create_figure(metric, df):
    plt.figure(figsize=(10, 6))
    # Check if 'timestamp' column exists in the dataframe
    if 'timestamp' in df.columns:
        # Make a copy of the dataframe to preserve the original
        df_copy = df.copy()
        # Convert 'timestamp' to datetime and set as index in the copy
        df_copy['timestamp'] = pd.to_datetime(df_copy['timestamp'])
        df_copy.set_index('timestamp', inplace=True)
        df_copy[metric].plot(kind='bar')
        plt.title(f'{metric} over Time')
        plt.xlabel('Time')
        plt.ylabel(metric)
        # Rotate x-axis labels for better readability
        plt.xticks(rotation=45)
        plt.tight_layout()
        img = BytesIO()
        plt.savefig(img, format='png')
        plt.close()
        img.seek(0)
        plot_url = base64.b64encode(img.getvalue()).decode('utf8')
        return plot_url
    else:
        # Log an error if 'timestamp' column is missing
        logging.error(f"'timestamp' column not found in dataframe for metric {metric}")
        return None

@app.route('/')
def dashboard():
    try:
        logging.info('Dashboard function called')
        conn = get_db_connection()
        df_performance = pd.read_sql_query("SELECT timestamp, cpm, cpc, roas FROM performance ORDER BY timestamp", conn)
        # Log the dataframe structure to verify the presence of 'timestamp' column
        logging.debug(f"Dataframe structure: {df_performance.columns.tolist()}")
        # Log the entire dataframe to verify data retrieval
        logging.debug(f"Dataframe contents: \n{df_performance.to_string()}")
        conn.close()

        # Log the dataframe structure before calling create_figure
        logging.debug(f"Dataframe structure before create_figure for cpm: {df_performance.columns.tolist()}")
        cpm_plot = create_figure('cpm', df_performance)
        # Log the dataframe structure before calling create_figure
        logging.debug(f"Dataframe structure before create_figure for cpc: {df_performance.columns.tolist()}")
        cpc_plot = create_figure('cpc', df_performance)
        # Log the dataframe structure before calling create_figure
        logging.debug(f"Dataframe structure before create_figure for roas: {df_performance.columns.tolist()}")
        roas_plot = create_figure('roas', df_performance)

        # Check if any of the plots could not be created
        if None in [cpm_plot, cpc_plot, roas_plot]:
            raise ValueError("One or more plots could not be created due to missing 'timestamp' column.")

        logging.info('Dashboard data prepared successfully')
        return render_template('dashboard.html', cpm_plot=cpm_plot, cpc_plot=cpc_plot, roas_plot=roas_plot)
    except Exception as e:
        logging.error('Error in dashboard function: %s', e)
        raise

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
