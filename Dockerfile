FROM python:3.13.12-slim-trixie

# Don’t create .pyc files -> .pyc files are compiled versions of Python files. Inside Docker, they’re usually unnecessary.
ENV PYTHONDONTWRITEBYTECODE=1

# print output immediately -> Without this, logs may not show instantly in Docker logs. Very useful for debugging.
ENV PYTHONUNBUFFERED=1

# All future commands will run inside the /app folder.
WORKDIR /app

# . -> /app -> ./
COPY requirements.txt . 

# -> built time
RUN pip install --upgrade pip 
RUN pip install -r requirements.txt

# host -> container
COPY . .


EXPOSE 8001

# -> runtime
# 0.0.0.0 - means  server inside the container will accept connections on all network interfaces with in the container
CMD [ "python", "manage.py", "runserver", "0.0.0.0:8000" ] 
