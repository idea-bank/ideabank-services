"""Tests for s3crud service class"""

from unittest.mock import patch
import pytest

from ideabank_webapi.services import S3Crud
from ideabank_webapi.config import ServiceConfig


class TestS3CrudService:
    def setup_method(self):
        self.s3 = S3Crud()

    @pytest.mark.parametrize("key, data", [
        ('path/to/key', b'data1'),
        ('name-to-key', b'data2')
        ])
    def test_put_item(self, key, data):
        with patch.object(self.s3, '_s3_client') as mock_s3:
            self.s3.put_item(key, data)
            mock_s3.put_object.assert_called_once_with(
                    Bucket=ServiceConfig.FileBucket.BUCKET_NAME,
                    Key=key,
                    Body=data,
                    ACL='private',
                    ContentType='image/*'
            )

    @pytest.mark.parametrize("key", ['path/to/key', 'name-to-key'])
    def test_share_item(self, key):
        with patch.object(self.s3, '_s3_client') as mock_s3:
            self.s3.share_item(key)
            mock_s3.generate_presigned_url.assert_called_once_with(
                    ClientMethod='get_object',
                    Params={
                        'Key': key,
                        'Bucket': ServiceConfig.FileBucket.BUCKET_NAME
                        },
                    ExpiresIn=self.s3.LINK_TLL
            )
