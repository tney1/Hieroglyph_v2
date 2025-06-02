FROM shell:dependencies

WORKDIR /opt/app/

COPY VERSION /opt/app/
COPY src/ /opt/app/src/
COPY setup.py /opt/app/
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0
RUN python /opt/app/setup.py develop

# CMD python /opt/app/src/hieroglyph/main.py

