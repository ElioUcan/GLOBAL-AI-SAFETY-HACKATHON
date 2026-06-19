FROM grafana/grafana:11.1.0

# MongoDB has no first-party Grafana datasource, so we install the community
# plugin at build time. It is unsigned, hence the allow-list env var in compose.
ENV GF_INSTALL_PLUGINS="https://github.com/haohanyang/mongodb-datasource/releases/latest/download/haohanyang-mongodb-datasource.zip;haohanyang-mongodb-datasource"

EXPOSE 3000
