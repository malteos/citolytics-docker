FROM jupyter/scipy-notebook

USER root

RUN set -x; \
  apt-get update \
  && apt-get install -y libmysqlclient-dev  mysql-client

USER $NB_USER

RUN pip2 install mysql-python tabulate matplotlib scipy pandas numpy --user

USER root
