# Use an official Python runtime as a parent image
FROM python:latest

LABEL author="amir jahangiri"
LABEL email="amirrj037@gmail.com"


# Set the working directory in the container
WORKDIR /src

# Copy the current directory contents into the container at /src
COPY . .


# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt


# Make port 80 available to the world outside this container
EXPOSE 80



# Define environment variable
ENV TELEGRAM_BOT_API_KEY="6861008650:AAHVadlu-rvR_K1Khn7siWNfsjgrX3fpHrc"


CMD ["python", "main.py"]


