import logging
import os
import sys
import re

LOG_LEVEL_DEFAULT = 3

LOG_LEVELS = [
    "critical",
    "error",
    "warning",
    "info",
    "debug",
    "trace"
]

LOG_FORMATS = {
    "default": "{asctime}.{msecs:03.0f} {name:20.20} [{module:>16s}:{lineno:<4}] [{levelname:>8s}] {message}",
    "compact": "{asctime} [{levelname:>8s}] {message}",
}

LOG_LEVEL_RE = re.compile(
    """
    (?:(?P<module>[^=,?&]+)=)?(?P<level>\w+)(?:\?([^,]+))?
    """
, re.VERBOSE)

LOG_PARAMS_RE = re.compile(
    r"""
    (?P<key>[^&,=]+)=?(?P<value>[^&,]+)?&?
    """
, re.VERBOSE)

def set_stream_log_level(stream, level, logger=None):

    if not logger:
        logger = logging.getLogger()

    for h in logger.handlers:
        if h.stream == stream:
            h.setLevel(level)


def add_log_handler(logger, handler, log_format=None):

    if not log_format:
        log_format = "default"

    date_format = "%Y-%m-%d %H:%M:%S"
    log_format = LOG_FORMATS.get(log_format, log_format)

    formatter = logging.Formatter(
        log_format,
        datefmt=date_format,
        style='{'
    )
    handler.setFormatter(formatter)
    if not isinstance(logger, logging.Logger):
        logger = logging.getLogger(logger)
    logger.addHandler(handler)


def add_logging_args(parser, short_args={}):

    parser.add_argument(
        short_args.get("log-config", "-l"),
        "--log-config",
        help="log level configuration"
    )

    group = parser.add_mutually_exclusive_group()

    group.add_argument(
        short_args.get("verbose", "-v"),
        "--verbose",
        action="count",
        default=0,
        help="verbose logging"
    )

    group.add_argument(
        short_args.get("verbose-max", "-V"),
        "--verbose-max",
        action="store_true",
        help="most verbose logging"
    )

    group.add_argument(
        short_args.get("quiet", "-q"),
        "--quiet",
        action="count",
        default=0,
        help="quiet logging"
    )

    group.add_argument(
        short_args.get("quiet-max", "-Q"),
        "--quiet-max",
        action="store_true",
        help="quietist logging"
    )


def parse_log_config(s):
    return [
        (
            logger_name,
            level,
            {
                k: v or None
                for k, v in LOG_PARAMS_RE.findall(params)
                if k
            }
        )
        for (logger_name, level, params)
        in LOG_LEVEL_RE.findall(s)
    ]


def adjust_level(level, args):

    if args.quiet_max:
        level = LOG_LEVELS[0]
    elif args.verbose_max:
        level = LOG_LEVELS[-1]
    elif level is None:
        level = LOG_LEVEL_DEFAULT

    if isinstance(level, str):
        level = next(i for i, l in enumerate(LOG_LEVELS) if l == level)

    level = level + args.verbose - args.quiet
    level = getattr(logging, LOG_LEVELS[level].upper())

    return level


def setup_logging(args, default_logger=None):

    TRACE_LEVEL_NUM = 9

    for level in LOG_LEVELS[:-1]:
        logging.addLevelName(getattr(logging, level.upper()), level)

    logging.addLevelName(TRACE_LEVEL_NUM, "trace")
    logging.TRACE = TRACE_LEVEL_NUM
    def trace(self, message, *args, **kws):
        if self.isEnabledFor(TRACE_LEVEL_NUM):
            self._log(TRACE_LEVEL_NUM, message, args, **kws)
    logging.Logger.trace = trace

    root_level = LOG_LEVEL_DEFAULT

    # configure root logger
    configure_logger(
        None, adjust_level(LOG_LEVEL_DEFAULT, args)
    )

    # configure any additional loggers
    if args.log_config:
        for logger, level, params in parse_log_config(args.log_config):
            # level = adjust_level(level, args)
            configure_logger(logger, level, params, default_logger=default_logger)



def configure_logger(logger, level, params={}, default_logger=None):

    if not isinstance(logger, logging.Handler):
        if logger == ".":
            logger = None
        elif logger is None:
            logger == default_logger

        logger = logging.getLogger(logger)

    if not {"stream", "file"} & set(params.keys()):
        params["stream"] = "stderr"

    logger.setLevel(level)

    log_format = params.pop("format", "default")

    for k, v in params.items():
        if k == "file":
            handler = logging.FileHandler(v)
            add_log_handler(logger, handler, log_format=log_format)
        elif k == "stream":
            handler = logging.StreamHandler(getattr(sys, v))
            add_log_handler(logger, handler, log_format=log_format)



__all__ = [
    "setup_logging",
    "add_logging_args",
    "set_stream_log_level",
    "add_log_handler"
]
