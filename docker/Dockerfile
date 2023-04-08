FROM tiangolo/uvicorn-gunicorn-fastapi:python3.9

# Building ARGS
ARG INSTALL_DEV=false

## Install Poetry
RUN cd /app/
RUN python -m pip install --upgrade pip
COPY requirements.txt /app/
RUN pip3 install -r requirements.txt
# RUN bash -c "if [ $INSTALL_DEV == 'true' ] ; then poetry install -vv; else poetry install --no-dev -vv; fi"

## Adding necessary scripts
COPY scripts/prestart.sh /app/

## Update Workdir
WORKDIR /app/app/
COPY ./app/ .
CMD ["/start.sh"]
