FROM mongo:7.0

# Pin a known-good MongoDB release for reproducible benchmark runs.
# Init scripts in /docker-entrypoint-initdb.d run once, on first container start
# (only when the data volume is empty).
COPY init/ /docker-entrypoint-initdb.d/

EXPOSE 27017
