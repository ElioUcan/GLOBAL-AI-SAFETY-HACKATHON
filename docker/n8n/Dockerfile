FROM n8nio/n8n:latest

# n8n runs as the unprivileged "node" user in the official image.
USER root

# MongoDB community node so workflows can read jerga / write results
# directly instead of going through raw HTTP. Optional but handy.
RUN cd /usr/local/lib/node_modules/n8n \
    && npm install n8n-nodes-mongodb --no-audit --no-fund || true

USER node

EXPOSE 5678
