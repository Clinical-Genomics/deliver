# -*- coding: utf-8 -*-
from sqlalchemy.orm.exc import NoResultFound


class DeliverError(Exception):

    def __init__(self, message: str=None):
        self.message = message


class MissingFlowcellError(NoResultFound, DeliverError):
    pass


class FastqFileMissingError(DeliverError):
    pass
