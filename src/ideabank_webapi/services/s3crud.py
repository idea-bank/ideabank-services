"""
    :module name: s3crud
    :module summary: Base service class for interacting with s3 compatible stores
    :module author: Nathan Mendoza (nathancm@uci.edu)
"""

import boto3
import botocore

from ..config import ServiceConfig


class S3Crud:
    """Class that interfaces with S3 storage provide CRUD operations
    Attributes:
        s3_client: connection to an s3 compatible stores
    """
    SHARE_TIME = 3600

    def __init__(self):
        self._s3_client = boto3.session.Session().client(
                's3',
                endpoint_url=ServiceConfig.FileBucket.BUCKET_HOST,
                config=botocore.config.Config(s3={'addressing_style': 'virtual'}),
                region_name=ServiceConfig.FileBucket.BUCKET_REGION,
                aws_access_key_id=ServiceConfig.FileBucket.BUCKET_KEY,
                aws_secret_access_key=ServiceConfig.FileBucket.BUCKET_SECRET
                )

    def put_item(self, key: str, data: bytes) -> None:
        """Put the given data in an s3 bucket with the gvien key
        Arguments:
            key: unique string that indexes the data. Can be path like
            data: raw data to be uploaded to the bucket
        """
        self._s3_session.put_object(
                Bucket=ServiceConfig.FileBucket.BUCKET_NAME,
                Key=key,
                Body=data,
                ACL='private',
                ContentType='image/*'
                )

    def share_item(self, key) -> str:
        """Provide a share link to object with the given key
        Arguments:
            key: string index of the object to share
        Returns:
            [str]: a url to access the object
        """
        return self._s3_session.generate_presigned_url(
                ClientMethod='get_object',
                Params={
                    'Bucket': ServiceConfig.FileBucket.BUCKET_NAME,
                    'Key': key
                    },
                ExpiresIn=self.SHARE_TIME
                )
