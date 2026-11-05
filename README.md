# Oracle Arena

**Oracle Arena** is a web application that hosts original player performance metrics, data visualizations, and predictive machine learning models based on NBA statistics.

## Overview

As sports betting and fantasy sports continue to grow, an increasing number of fans are interested in advanced analytics. Oracle Arena gives NBA fans access to the statistical analysis tools they need to deepen their understanding of the game: original performance metrics, data visualizations, and predictive machine learning.

## Background

As sports betting and fantasy sports grow, so does interest in advanced analytics. Fans want to further their understanding of the sport in order to gain an edge when betting on games or simply to discuss the teams and players they love in greater detail.

Oracle Arena was created to meet this interest by developing a web application with the statistical analysis tools NBA fans need.

## Features

- **Original performance metrics** — metrics that represent a player's ability to defend, shoot, rebound, etc. better than simple volume statistics.
- **Data visualizations** — visualizations that present these statistics for large groups of players.
- **Win prediction** — a machine learning model that predicts the winner of NBA games at a high rate.
- **Betting assistant** — as a feature of the win prediction model, helps users determine the quality of a bet based on the odds of the bet and the confidence of the model's prediction.

## Final Deliverables

This folder contains the core documentation and presentation materials submitted for the Oracle Arena senior design project. These files provide detailed insight into the project's objectives, technical implementation, and final results.

- [`Oracle_Arena_Final_Report.pdf`](final-deliverables/Oracle_Arena_Final_Report.pdf)
  - A 17-page technical report detailing the full scope of the project, including background research, system design, data pipeline, model architecture, testing, results, and conclusions.

- [`Data_ML_Architecture_Presentation.pdf`](final-deliverables/Data_ML_Architecture_Presentation.pdf)
  - A slide presentation outlining the data collection and storage process, feature engineering steps, and an in-depth overview of the machine learning models used in the project.

- [`Senior_Design_Showcase_Poster.pdf`](final-deliverables/Senior_Design_Showcase_Poster.pdf)
  - The final academic poster presented during the Senior Design Showcase, summarizing the project's motivation, methodology, results, and key takeaways in a visual format.

## Technical Stack

- **Frontend:** Next.js 15 (App Router), React 18, TypeScript, Tailwind CSS, TanStack React Table, Axios.
- **Backend:** Django 5.2 LTS, served by Gunicorn, backed by PostgreSQL, with CORS support; containerized with Docker.
- **Data:** Python tooling for scraping and importing data from sources such as Basketball Reference and Basketball Index.
- **Machine Learning:** Python, TensorFlow, Keras, scikit-learn, XGBoost, pandas, NumPy, SciPy, and joblib; trained model artifacts are stored in `ml/models`.

## Getting Started

The application is deployed at [https://courtoracle.fyi](https://courtoracle.fyi).

### Prerequisites

- Node.js (for the frontend)
- Docker (for the backend and database)

### Frontend

The frontend is a Next.js application located in the `frontend/` directory.

#### Local development

```bash
git clone https://github.com/TritonEden/Oracle-Arena.git
cd Oracle-Arena/frontend
npm install
npm run dev
```

The default home page is served at `http://localhost:3000/home`.

#### Production build

```bash
cd frontend
npm run build
npm start
```

This will show which pages are static and server rendered and whether any errors need to be fixed before deploying the website.

### Backend

The backend runs locally through Docker.

1. Install Docker and Git (if not already installed).

2. From the repository root, run the following commands:

   ```bash
   cd Oracle-Arena

   # Build and run
   docker compose up --build

   # Run
   docker compose up

   # Stop
   docker compose down
   ```

   **Extra steps if compose isn't working:**

   ```bash
   docker build -t oracle-arena -f Azure-dockerfile .
   ```

   **Use for dev environment** to mount the local backend to the Docker container; useful for testing code without needing to rebuild each time:

   ```bash
   docker run --name oracle-arena --env-file .env \
     -p 8000:8000 -p 80:80 \
     -v $(pwd -W)/backend:/app/backend \
     -it oracle-arena
   ```

   After the initial run, a Docker container named `oracle-arena` will be created. Once closed, the container can be started again with:

   ```bash
   docker start oracle-arena
   ```

   **Use for production:**

   ```bash
   docker run --env-file .env -p 8000:8000 -p 80:80 -it oracle-arena
   ```

3. In a separate terminal, run the following commands to shell into the Docker container:

   ```bash
   # One line to shell into the container
   docker exec -it $(docker ps --filter "ancestor=oracle-arena" --format "{{.ID}}" | head -n 1) /bin/bash

   # Lists containers, copy the container_id for the oracle-arena image
   docker ps
   # Shell into the container
   docker exec -it <container_id> /bin/bash
   ```

4. Open your browser and go to `http://localhost:8000/` to see the backend of the web application.

5. Open your browser and go to `http://localhost:3000/home` to see the frontend of the web application.

## Project Scope

### Data Collection

- Scrape and/or import data from websites like Basketball Reference and Basketball Index.
- Live data updates to the models and performance metrics whenever the stats that affect them are updated.

### Web Frontend

- Simple UI to prevent new users from having issues accessing stats.
- Dynamic data visualization based on filters set by the user.

### Machine Learning

- The metrics that best determine who will win a game in the modern NBA are found via several different machine learning methods.
- Prediction of the winner of upcoming NBA games using the statistics found via the previous methods.

### Original Performance Metrics

- Original performance metrics users can access to give them a broader understanding of a player's ability in specific aspects of NBA basketball.

## Deliverables

1. A functional web application that can access the web pages that host the analytics tools.
2. Documentation describing the design process of the web app and tools.
3. Documentation describing the methods for data collection, data processing, what data was used for model training, reasoning behind the calculation of original performance metrics, and data visualization features.
