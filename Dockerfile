FROM \
    ssidk/bifrost-base:2.0.5

LABEL \
    name="bifrost-ssi_stamper_check" \
    description="Docker environment for ssi_stamper in bifrost" \
    version="2.0.5" \
    DBversion="31/07/19" \
    maintainer="kimn@ssi.dk;"

RUN \
    cd /bifrost; \
    git clone https://github.com/ssi-dk/bifrost-ssi_stamper.git ssi_stamper;

ENTRYPOINT \
    [ "/bifrost/whats_my_species/launcher.py"]
CMD \
    [ "/bifrost/whats_my_species/launcher.py", "--help"]