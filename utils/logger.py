import logging

logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def logger_raise_warn_exception(error_post_data, exception_type, detail):
    logger.warning(f'{detail}')
    logger.warning(error_post_data)
    raise exception_type(detail=detail)

def logger_info(*args):
    for info in args:
        logger.info(info)
