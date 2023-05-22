"""
    :module name: config
    :module summary: a unified place to get configurable values for the service
    :module author: Nathan Mendoza (nathancm@uci.edu)
"""

import os
from dotenv import load_dotenv

load_dotenv()


class ServiceConfig:  # pylint:disable=too-few-public-methods
    """Class containing config data for the service to operate"""

    class DataBase:  # pylint:disable=too-few-public-methods
        """Database related options"""
        DBHOST = os.getenv('DBHOST')
        DBPORT = os.getenv('DBPORT')
        DBUSER = os.getenv('DBUSER')
        DBPASS = os.getenv('DBPASS')
        DBNAME = os.getenv('DBNAME')

    class FileBucket:  # pylint:disable=too-few-public-methods
        """Content related options"""
        BUCKET_HOST = os.getenv('S3HOST')
        BUCKET_REGION = os.getenv('S3REGION')
        BUCKET_KEY = os.getenv('S3KEY')
        BUCKET_SECRET = os.getenv('S3SECRET')
        BUCKET_NAME = os.getenv('S3NAME')

    class AuthKey:  # pylint:disable=too-few-public-methods
        """JWT related options"""
        JWT_SIGNER = os.getenv('JWT_SIGNER')
        JWT_HASHER = os.getenv('JWT_HASHER')
        AUTH_URL = os.getenv('AUTH_URL')
