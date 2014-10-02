docker-status
=============

A Docker app that checks the HTTP status of linked containers. Will
automatically poll all linked containers that expose port 80, and will respond
to HTTP requests with a 200 status if all linked containers are OK or a 500
otherwise.

This is designed to be used, for example, with AWS ELB health checks to
determine if any application has failed on instances which are running multiple
web apps in Docker containers.

The app exposes port 80, so the idea is to make this app the default in Nginx
(or whatever you're using) if no hostname is specified.

Example:

    docker run -d --link app1:app1 --link app2:app2 zooniverse/docker-status

Configuration can be done with environment variables:

    docker run -d --link app1:app1 -e "APP1_GET_PATH=/status" -e "HTTP_TIMEOUT=15" zooniverse/docker-status

Valid options are:

* *[NAME]_GET_PATH* – What path to get when testing the container *NAME*.
  **Default: /**
* *HTTP_TIMEOUT* – How many seconds to wait for each container to respond before
  assuming it has failed. **Default: 30**
* *TEST_INTERVAL* – How often to test linked containers (in seconds). **Default:
  30**
* *LISTEN_HOST* – Which IP address to listen on. Leave this alone unless
  you're doing something interesting with the --net option to docker run.
  **Default: all (0.0.0.0)**
* *LISTEN_PORT* – Which port to listen on. Make sure to also expose the port
  if you change this. **Default: 80**
* *DEBUG* – Run Flask in debug mode. **Default: false**
