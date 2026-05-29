#Creating a docker file to setup mongodb locally
FROM mongo:latest
# Expose the default MongoDB port
EXPOSE 27017
# Set the default command to run MongoDB
CMD ["mongod"]
#why we didnt mentioned /data/db ? 
# In the official MongoDB Docker image, the default data directory is set to /data/db. When you run the container, it automatically uses this directory for storing MongoDB data. Therefore, you don't need to explicitly mention it in the Dockerfile unless you want to change the default behavior or specify a different data directory. By using the default settings, you can simply run the container without additional configuration, and MongoDB will store its data in /data/db as intended.

