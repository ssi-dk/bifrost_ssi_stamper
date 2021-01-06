# This is intended to run in Local Development (dev) and Github Actions (test/prod)
# BUILD_ENV options (dev, test, prod) dev for local testing and test for github actions testing on prod ready code
ARG BUILD_ENV="prod"
ARG BIFROST_COMPONENT_NAME="bifrost_ssi_stamper"
ARG MAINTAINER="kimn@ssi.dk;"
ARG FORCE_DOWNLOAD=true

#---------------------------------------------------------------------------------------------------
# Programs for all environments
#---------------------------------------------------------------------------------------------------
FROM continuumio/miniconda3:4.8.2 as build_base
ARG BUILD_ENV
ARG BIFROST_COMPONENT_NAME
ARG MAINTAINER
ARG FORCE_DOWNLOAD
LABEL \
    BIFROST_COMPONENT_NAME=${BIFROST_COMPONENT_NAME} \
    description="Docker environment for ${BIFROST_COMPONENT_NAME}" \
    environment="${BUILD_ENV}" \
    maintainer="${MAINTAINER}"
RUN \
    conda install -yq -c conda-forge -c bioconda -c default snakemake-minimal==5.7.1;

#---------------------------------------------------------------------------------------------------
# Base for dev environement
#---------------------------------------------------------------------------------------------------
FROM continuumio/miniconda3:4.8.2 as build_dev
ARG BIFROST_COMPONENT_NAME
COPY --from=build_base / /
COPY /components/${BIFROST_COMPONENT_NAME} /bifrost/components/${BIFROST_COMPONENT_NAME}
COPY /lib/bifrostlib /bifrost/lib/bifrostlib
WORKDIR /bifrost/components/${BIFROST_COMPONENT_NAME}/
RUN \
    pip install -r requirements.txt; \
    pip install --no-cache -e file:///bifrost/lib/bifrostlib; \
    pip install --no-cache -e file:///bifrost/components/${BIFROST_COMPONENT_NAME}/

#---------------------------------------------------------------------------------------------------
# Base for production environment
#---------------------------------------------------------------------------------------------------
FROM continuumio/miniconda3:4.8.2 as build_prod
ARG BIFROST_COMPONENT_NAME
COPY --from=build_base / /
WORKDIR /bifrost/components/${BIFROST_COMPONENT_NAME}
COPY ./ ./
RUN \
    pip install file:///bifrost/components/${BIFROST_COMPONENT_NAME}/

#---------------------------------------------------------------------------------------------------
# Base for test environment (prod with tests)
#---------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------
FROM continuumio/miniconda3:4.8.2 as build_test
ARG BIFROST_COMPONENT_NAME
ARG BUILD_ENV
COPY --from=build_base / /
WORKDIR /bifrost/components/${BIFROST_COMPONENT_NAME}
COPY ./ ./
RUN \
    pip install -r requirements.txt \
    pip install file:///bifrost/components/${BIFROST_COMPONENT_NAME}/


#---------------------------------------------------------------------------------------------------
# Additional resources
#---------------------------------------------------------------------------------------------------
FROM build_${BUILD_ENV}
# NA

#---------------------------------------------------------------------------------------------------
# Run and entry commands
#---------------------------------------------------------------------------------------------------
WORKDIR /bifrost/components/${BIFROST_COMPONENT_NAME}
ENTRYPOINT ["python3", "-m", "bifrost_ssi_stamper"]
CMD ["python3", "-m", "bifrost_ssi_stamper", "--help"]
