import logging


def get_logger(logger_name, level=logging.INFO, create_file: bool = False):

  log = logging.getLogger(logger_name)
  log.setLevel(level=logging.DEBUG)

  formatter = logging.Formatter(
    '%(asctime)s: [%(name)s][%(levelname)s] --- %(message)s')

  if create_file:
    fh = logging.FileHandler('StrAnno.log', encoding='utf-8')
    fh.setLevel(level=level)
    fh.setFormatter(formatter)

  ch = logging.StreamHandler()
  ch.setFormatter(formatter)
  ch.setLevel(level=level)

  if create_file:
    log.addHandler(fh)

  log.addHandler(ch)
  return log
