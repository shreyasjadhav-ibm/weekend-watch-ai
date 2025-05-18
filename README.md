# WeekendWatchAI

## Project Overview

**WeekendWatchAI** is an AI-driven agent designed to monitor and support application operations during off-peak hours, such as weekends. It processes logs from a full-stack system (React frontend and Python/Java backend) to detect anomalies and provide automated resolutions. The system uses:

- **Model 1**: A RandomForestClassifier to classify logs as anomalous or normal based on features like log messages and anomaly types.
- **Model 2**: The Google Gemini API to generate fixes or suggestions for anomalies when requested by the user.
- **Flask API**: Handles log ingestion, anomaly detection, user prompts, and fix generation.

The project processes logs (e.g., `"ERROR: TypeError: Cannot read property 'map' of undefined"`, `"ERROR: Failed to connect to PostgreSQL database"`) from CSV files or log aggregators, enabling proactive issue resolution to ensure system reliability.

## Required Libraries

To run the project, install the following Python libraries:

- `pandas`: For CSV log processing.
- `scikit-learn`: For the RandomForestClassifier (anomaly detection).
- `joblib`: For saving/loading the trained model.
- `flask`: For the API server.
- `requests`: For Gemini API calls.
- `python-dotenv`: For loading environment variables (e.g., Gemini API key).

Install them using:
```bash
pip install pandas scikit-learn joblib flask requests python-dotenv
```

## How to Run the Repository

Follow these steps to set up and run **WeekendWatchAI**:

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/yourusername/weekend-watch-ai.git
   cd weekend-watch-ai
   ```

2. **Set Up Environment Variables**:
   - Create a `.env` file in the project root:
     ```plaintext
     GEMINI_API_KEY=your-api-key-here
     ```
   - Obtain a Gemini API key from [Google AI Studio](https://aistudio.google.com/) or Google Cloud Console.
   - Ensure `.env` is listed in `.gitignore` to avoid committing sensitive data.

3. **Train the RandomForestClassifier**:
   - Place your log CSV (e.g., `logs.csv`) in the project root.
   - Run the training script to generate the model:
     ```bash
     python train_random_forest.py
     ```
   - This creates `random_forest_model.pkl` for anomaly detection.

5. **Run the Flask API**:
   - Start the Flask server:
     ```bash
     python app.py
     ```
   - The API will be available at `http://localhost:5000`.

6. **Monitor and Interact**:
   - The API flags anomalies and prompts for fixes. Integrate with a UI (e.g., React) to display prompts and trigger `/api/fix-log` when users choose to fix.
   - Alerts (e.g., Slack, email) can be configured for critical anomalies or fix outcomes.

## Notes
- Ensure your CSV logs have columns: `timestamp`, `log_message`, `is_anomaly`, `anomaly_type`.
- The RandomForestClassifier requires sufficient labeled data (`is_anomaly`) for training.
- Secure the Gemini API key using environment variables or a secret manager.
