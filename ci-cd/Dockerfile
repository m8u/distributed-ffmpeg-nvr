ARG CI_APPLICATION_REPOSITORY
ARG ENVIRONMENT

FROM ${CI_APPLICATION_REPOSITORY}:base-${ENVIRONMENT}

WORKDIR /app

COPY . .

ENTRYPOINT ["sh", "ci-cd/docker-entrypoint.sh"]
