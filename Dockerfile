FROM python:3.6-stretch

RUN apt-get update && apt-get install -y git gcc python3-dev make portaudio19-dev libsamplerate0-dev libspeex-dev libspeexdsp-dev

COPY requirements.txt /opt/requirements.txt
COPY test_requirements.txt /opt/test_requirements.txt
RUN pip install numpy scipy
RUN pip install -r /opt/requirements.txt

RUN mkdir /workdir

WORKDIR /opt
COPY setup.py /opt/setup.py
COPY tuxeatpi_speech_nuance /opt/tuxeatpi_speech_nuance
RUN python setup.py install

WORKDIR /workdir

COPY dialogs /dialogs
COPY intents /intents

ENTRYPOINT ["tep-speech-nuance", "-w", "/workdir", "-I", "/intents", "-D", "/dialogs"]
