docker-status
=============

A Docker app that checks the HTTP status of linked containers. Will
automatically poll all linked containers that expose port 80, and will respond
to HTTP requests with a 200 status if all linked containers are OK or a 500
otherwise.

This is designed to be used, for example, with AWS ELB health checks to
determine if any application has failed on instances which are running multiple
apps in Docker containers.
