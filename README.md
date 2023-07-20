# Data Hackathons
Python webapp that allows people to host and participate to kaggle-style competitions.

# Getting started
To test locally, you will need to:
- clone the repository
- install the dependencies `poetry install`
- create a `.env` file with configuration, (can copy the template: `cp .env.template .env`
- start the server with `poetry run python scripts/run_local.py`
- (optional) from another terminal, setup some sample data `poetry run python scripts/send_sample_data.py`
- open the browser on http://localhost:8000

# Deployment
Currently only Azure Web App with Microsoft managed Auth is supported.
