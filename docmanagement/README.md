# ChatIFC Studio: Document Management and Data Ingestion APIs

## Description
Document Management is a FastAPI backend application hosted on Azure App Services. It provides a set of RESTful APIs for managing operations for the documents and performing data ingestion.

## Installation

### Prerequisites
- Python 3.9+
- pip (Python package installer)

### Steps
1. Clone the repository:
    ```sh
    cd <your_project_path>
    https://IFC-CIT-Org@dev.azure.com/IFC-CIT-Org/IFC-CIT-GenAI-Accelerator/_git/genai-accel-services-docmgmt
    cd <your_project_path>/genai-accel-services-docmgmt
    ```


2. Create a virtual environment:
    ```sh
    python -m venv <your_environment_name>
    cd <your_environment_name>/Scripts/activate
    
    ```


3. Install the dependencies:
    ```sh
    cd <your_project_path>/genai-accel-services-docmgmt
    pip install -r requirements.txt
    
    ```

## Usage

### Running the Application Locally
1. Start the FastAPI server:
    ```sh
    
    python -m uvicorn src.server:app --reload --host localhost --port <8000/3000/3001/3002>
    
    ```

2. Open your browser and navigate to `http://localhost:<your_port>/docs` to access the Swagger UI for API documentation.

3. Enable local settings
   - Open 'core/config.py'
   - set DEBUG = True

## Shipping your features

1. Switch to Dev branch on your local (`git checkout Dev`)
2. Create a new (feature) branch (`git checkout -b <your_feautre_ticket>-description`).
3. Make your changes.
4. Commit your changes (`git commit -m 'Add some feature'`).
5. Push to the branch (`git push origin feature/<your_feautre_ticket>-description`).
6. Raise a pull request to push your changes from feature branch to `Dev` branch and request for an approval on the same.

## CI/CD
### DEV
- When the build is successful on `Dev` branch, it will automatically start the Release pipeline.
### QA
- When deployment is finished on `Dev` branch, raise a new PR to push your changes from `Dev` to `Release` branch.
- 2 approvals are required for the movement to `Release` branch.
- When the build is successful on `Release` branch, request for deployment.
- The deployment will begin once the approval is provided.
