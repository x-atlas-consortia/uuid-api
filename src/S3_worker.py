import logging
import time
import boto3
from botocore.exceptions import ClientError

class S3Worker:

    '''
    def __init__(self, app_config=None):

        self.logger = logging.getLogger('uuid.service')

        if app_config is None:
            raise Exception("Configuration data loaded by the app must be passed to the worker.")
        try:
            self.aws_access_key_id = app_config['AWS_ACCESS_KEY_ID']
            self.aws_secret_access_key = app_config['AWS_SECRET_ACCESS_KEY']
            self.aws_s3_bucket_name = app_config['AWS_S3_BUCKET_NAME']
            self.aws_object_url_expiration_in_secs = app_config['AWS_OBJECT_URL_EXPIRATION_IN_SECS']
        except KeyError as ke:
            self.logger.error(f"Expected configuration failed to load {ke} from app_config={app_config}.")
            raise Exception("Expected configuration failed to load. See the logs.")

        try:
            self.s3resource = boto3.Session(
                self.aws_access_key_id,
                self.aws_secret_access_key
            ).resource('s3')
            # try an operation just to verify the Resource works so that the except clause
            # is entered here rather than another method if configuration is not correct.
            self.s3resource.meta.client.head_bucket(Bucket=self.aws_s3_bucket_name)
        except ClientError as ce:
            self.logger.error(f"Unable to access S3 Resource. ce={ce} with app_config={app_config}.")
            raise Exception("Expected resource failed to load. See the logs.")

        self.logger.debug(f"self.s3resource={self.s3resource}")
    '''

    def __init__(self, theAWS_ACCESS_KEY_ID, theAWS_SECRET_ACCESS_KEY, theAWS_S3_BUCKET_NAME, theAWS_OBJECT_URL_EXPIRATION_IN_SECS):

        self.logger = logging.getLogger('uuid.service')

        try:
            self.aws_access_key_id = theAWS_ACCESS_KEY_ID
            self.aws_secret_access_key = theAWS_SECRET_ACCESS_KEY
            self.aws_s3_bucket_name = theAWS_S3_BUCKET_NAME
            self.aws_object_url_expiration_in_secs = theAWS_OBJECT_URL_EXPIRATION_IN_SECS
        except KeyError as ke:
            self.logger.error(f"Expected configuration failed to load {ke} from constructor parameters.")
            raise Exception("Expected configuration failed to load. See the logs.")

        try:
            self.s3resource = boto3.Session(
                self.aws_access_key_id,
                self.aws_secret_access_key
            ).resource('s3')
            # try an operation just to verify the Resource works so that the except clause
            # is entered here rather than another method if configuration is not correct.
            self.s3resource.meta.client.head_bucket(Bucket=self.aws_s3_bucket_name)
        except ClientError as ce:
            self.logger.error(f"Unable to access S3 Resource. ce={ce} with app_config={app_config}.")
            raise Exception("Expected resource failed to load. See the logs.")

        self.logger.debug(f"self.s3resource={self.s3resource}")

    def stash_text_as_object(self, theText, aUUID):
        large_response_bucket = self.s3resource.Bucket(self.aws_s3_bucket_name)
        object_key = f"{aUUID}_{len(theText)}_{str(time.time())}"
        obj = large_response_bucket.Object(object_key)
        try:
            obj.put(Body=theText)
            return object_key
        except ClientError as ce:
            self.logger.error(f"Unable to upload to {self.aws_s3_bucket_name}. ce={ce}.")
            raise Exception("Large response creation failed. See the logs.")

    def create_URL_for_object(self, object_key):
        try:
            response = self.s3resource.meta.client.generate_presigned_url('get_object',
                                                                          Params={'Bucket': self.aws_s3_bucket_name,
                                                                                  'Key': object_key},
                                                                          ExpiresIn=self.aws_object_url_expiration_in_secs)
            self.logger.debug(f"presigned url response={response}")
            return response
        except ClientError as ce:
            self.logger.error(f"Unable generate URL to {self.aws_s3_bucket_name}. ce={ce}.")
            raise Exception("Generation of link to large response failed. See the logs.")

