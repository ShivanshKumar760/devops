#Fetch a base image of nodejs for our basic api-layer 1
FROM node:20-slim
#now our api also have mongodb so can in one container we can run both node and mongodb but it is not a good practice to run multiple services in one container so we will use docker-compose to run multiple containers for our api and mongodb
#but for the sake of simplicity we will run both node and mongodb in one container but it is not a good practice to run multiple services in one container so we will use docker-compose to run multiple containers for our api and mongodb

#lets get a mongodb image and run it in the same container
#install mongodb in our container
RUN apt-get update && apt-get install -y \
    gnupg \
    curl \
    && curl -fsSL https://www.mongodb.org/static/pgp/server-7.0.asc | \
       gpg --dearmor -o /usr/share/keyrings/mongodb-server-7.0.gpg \
    && echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/debian bookworm/mongodb-org/7.0 main" \
       | tee /etc/apt/sources.list.d/mongodb-org-7.0.list \
    && apt-get update \
    && apt-get install -y mongodb-org \
    && rm -rf /var/lib/apt/lists/*
#what is the above command doing?
#the above command is installing mongodb in our container using apk package manager which is used in alpine linux
#now we have mongodb installed in our container but we need to start mongodb and our nodejs server when the container starts


# Create the MongoDB data directory (required for mongod to start)
RUN mkdir -p /data/db
#Set the working directory to /app
WORKDIR /app

#Copy the package.json and package-lock.json files to the working directory
COPY package*.json ./

#Install the dependencies
RUN npm install

#Copy the rest of the application code to the working directory
COPY . .

#Expose the port on which our api will run
EXPOSE 3000

#Expose the port on which mongodb will run
EXPOSE 27017

# Start script: Start MongoDB in the background, then start Node
CMD ["sh", "-c", "mongod --bind_ip_all --fork --logpath /var/log/mongodb.log && node index.js"]