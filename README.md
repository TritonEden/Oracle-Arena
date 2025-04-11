# Oracle-Arena

Oracle Arena - A web application that hosts original player performance metrics, data visualizations, and predictive machine learning models based on NBA statistics.

## Background

As sports betting and fantasy sports grow, there is an increasingly large group of sports fans interested in advanced analytics. Fans want to further their understanding of sports in order to gain an upper hand when betting on games or simply to discuss the sports they love in further detail. This project seeks to develop a web application with the statistical analysis tools NBA fans need to increase their understanding of the league.

## Setup for webpage (frontend)

1. Install NodeJS
2. (Optional): Install VSCode Extensions (ES7+ React, Javascript and Typescript, Tailwind CSS IntelliSense).
3. Run the following commands:

```bash
git clone https://github.com/TritonEden/Oracle-Arena.git
cd Oracle-Arena
cd frontend
npm install
npm run dev
```

The default home page is `http://localhost:3000/home`. Go to there to see the default webpage.
Another way to actually see the production side of the webpage is to run the following commands:

```bash
cd frontend
npm run build
npm start
```

This will show which pages are static and server rendered and to see if we need to fix on any errors before deploying this website

## Setup for Docker backend

1. Install docker and git (if not already installed)
2. In your terminal, run the following commands:

```bash
cd Oracle-Arena
docker build -t oracle-arena -f Azure-dockerfile .

## Use for Dev environment to mount local backend to docker container
## Useful for testing code without needing to rebuild each time
docker run --name oracle-arena --env-file .env \
  -p 8000:8000 -p 3000:3000 -p 80:80 \
  -v $(pwd -W)/backend:/app/backend \
  -it oracle-arena \

## After the initial run command a docker container called 'oracle-arena' will be created
# Once closed the container can be started again with:
docker start oracle-arena 

## Use for production
docker run --env-file .env -p 8000:8000 -p 80:80 -it oracle-arena 
```

3. In a separate terminal, run the following commands to shell into the Docker container:

```bash

# One Line to shell into the container
docker exec -it $(docker ps --filter "ancestor=oracle-arena" --format "{{.ID}}" | head -n 1) /bin/bash


# Lists containers, copy the container_id for the oracle-arena image
docker ps
# Shell into the container
docker exec -it <container_id> /bin/bash
```


4. Open your browser and go to `http://localhost:8000/` to see the backend of the web application.

5. Open your browser and go to `http://localhost:3000/home` to see the frontend of the web application.

## Project Needs

1. Design a sleek and easy to use web frontend so users can find the stats they want quickly.
2. Develop a machine learning model that predicts the winner of NBA games at a high rate.
3. As a feature of the win prediction model, develop a betting assistant that helps users determine the quality of a bet based on the odds of the bet and the confidence of the model’s prediction.
4. Use advanced stats to create original metrics that represent a player's ability to defend, shoot, rebound, etc. better than simple volume statistics.
5. Create data visualizations to present these statistics for large groups of players.

## Project Scope

1. Data Collection:

* Scrape and/or import data from websites like Basketball Reference and Basketball Index.
* Live data updates to our models and our performance metrics whenever the stats that affect them are updated.

2. Web Frontend:

* Simple UI to prevent new users from having issues accessing stats
* Dynamic data visualization based on filters set by the user

3. Machine Learning Algorithm:

* The metrics that best determine who will win a game in the modern NBA are found via several different machine learning methods
* Prediction of the winner of upcoming NBA games using the statistics found in via the previous methods

4. Original Performance Metrics

* Original performance metrics users can access to give them a more broad understanding of a player’s ability in specific aspects of NBA basketball

## Potential Technical Considerations

1. Data Collection:

* Programming Languages: Python and R
* Web Scraping Libraries: Beautiful Soup
  * Database management system (MySQL)

2. Web Frontend:

* Front-end framework: React, Angular, etc.
* Back-end framework: Node.js

3. Machine Learning Algorithm:

* Programming Languages: Python
* Machine learning libraries: SciKit-learn, Pytorch, and TensorFlow

4. Original Performance Metrics

* Programming Languages: Python or R

## Deliverables

1. A functional web application that can access the web pages that host the analytics tools
2. Documentation describing the design process of the web app and tools
3. Documentation describing the methods for data collection, data processing, what data was used for model training, reasoning behind the calculation of original performance metrics, and data visualization features

Assumptions and Dependencies:
TBD
