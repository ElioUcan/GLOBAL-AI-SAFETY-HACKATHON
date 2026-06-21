FROM ghcr.io/berriai/litellm:main-stable

COPY config/litellm_config.yaml /app/config/litellm_config.yaml

EXPOSE 4000

CMD ["--config", "/app/config/litellm_config.yaml", "--port", "4000", "--host", "0.0.0.0"]
