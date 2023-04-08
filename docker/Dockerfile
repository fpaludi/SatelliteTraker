FROM tiangolo/uvicorn-gunicorn-fastapi:python3.9

# Building ARGS
ARG INSTALL_DEV=false

## Install Dependencies
RUN cd /app/
RUN python -m pip install --upgrade pip
COPY requirements.txt requirements_dev.txt /app/
RUN pip3 install -r requirements.txt
RUN bash -c "if [ $INSTALL_DEV == 'true' ] ; then pip3 install -r requirements_dev.txt; fi"

## Adding necessary scripts
COPY scripts/prestart.sh /app/

## Update Workdir
WORKDIR /app/app/
COPY ./app/ .
CMD ["/start.sh"]
