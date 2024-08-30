# pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib
# pip install oauth2client
# pip install httplib2

import os
import random
import time
import argparse
from pathlib import Path

import logging
from logging.handlers import TimedRotatingFileHandler

import http.client
import httplib2
import pickle

#from datetime import datetime, timedelta

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

class YoutubeUpload():
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

        # The CLIENT_SECRETS_FILE variable specifies the name of a file that contains
        # the OAuth 2.0 information for this application, including its client_id and
        # client_secret. You can acquire an OAuth 2.0 client ID and client secret from
        # the Google API Console at
        # https://console.developers.google.com/.
        # Please ensure that you have enabled the YouTube Data API for your project.
        # For more information about using OAuth2 to access the YouTube Data API, see:
        #   https://developers.google.com/youtube/v3/guides/authentication
        # For more information about the client_secrets.json file format, see:
        #   https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
        self.CLIENT_SECRETS_FILE = "client_secrets.json"

        # This OAuth 2.0 access scope allows an application to upload files to the
        # authenticated user's YouTube channel, but doesn't allow other types of access.
        self.YOUTUBE_UPLOAD_SCOPE = ["https://www.googleapis.com/auth/youtube", "https://www.googleapis.com/auth/youtube.upload"]
        self.YOUTUBE_API_SERVICE_NAME = "youtube"
        self.YOUTUBE_API_VERSION = "v3"

        # Maximum number of times to retry before giving up.
        self.MAX_RETRIES = 10

        # Always retry when these exceptions are raised.
        self.RETRIABLE_EXCEPTIONS = (httplib2.HttpLib2Error,
                                IOError,
                                http.client.NotConnected,
                                http.client.IncompleteRead,
                                http.client.ImproperConnectionState,
                                http.client.CannotSendRequest,
                                http.client.CannotSendHeader,
                                http.client.ResponseNotReady,
                                http.client.BadStatusLine)

        # Always retry when an apiclient.errors.HttpError with one of these status
        # codes is raised.
        self.RETRIABLE_STATUS_CODES = [500, 502, 503, 504]

        self.service = None

    def get_authenticated_service(self):
        creds = None
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)

        if not creds or not creds.valid or not creds.has_scopes(self.YOUTUBE_UPLOAD_SCOPE):
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())

            else:
                flow = InstalledAppFlow.from_client_secrets_file(self.CLIENT_SECRETS_FILE, self.YOUTUBE_UPLOAD_SCOPE)
                creds = flow.run_local_server(port=0, open_browser=False)
            
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)

        self.service = build(self.YOUTUBE_API_SERVICE_NAME, self.YOUTUBE_API_VERSION, credentials=creds)

    def initialize_upload(self, options):
        tags = None
        if options.keywords:
            tags = options.keywords.split(",")

        body = dict(
            snippet=dict(
                title=options.title,
                description=options.description,
                tags=tags,
                categoryId=options.category,
                defaultLanguage="ja",
                defaultAudioLanguage="ja",
            ),
            status=dict(
                privacyStatus=options.privacyStatus
            )
        )

        # Call the API's videos.insert method to create and upload the video.
        insert_request = self.service.videos().insert(
            part=",".join(body.keys()),
            body=body,
            # The chunksize parameter specifies the size of each chunk of data, in
            # bytes, that will be uploaded at a time. Set a higher value for
            # reliable connections as fewer chunks lead to faster uploads. Set a lower
            # value for better recovery on less reliable connections.
            #
            # Setting "chunksize" equal to -1 in the code below means that the entire
            # file will be uploaded in a single HTTP request. (If the upload fails,
            # it will still be retried where it left off.) This is usually a best
            # practice, but if you're using Python older than 2.6 or if you're
            # running on App Engine, you should set the chunksize to something like
            # 1024 * 1024 (1 megabyte).
            media_body=MediaFileUpload(options.mp4, chunksize=-1, resumable=True)
        )

        return self._resumable_upload(insert_request)

    # This method implements an exponential backoff strategy to resume a
    # failed upload.
    def _resumable_upload(self, insert_request):
        response = None
        error = None
        retry = 0
        while response is None:
            try:
                self.logger.info("Uploading file...")
                status, response = insert_request.next_chunk()
                if response is not None:
                    if 'id' in response:
                        self.logger.info("Video id '%s' was successfully uploaded." % response['id'])
                    else:
                        self.logger.error("The upload failed with an unexpected response: %s" % response)
                        exit(code=-1)
            except HttpError as e:
                if e.resp.status in self.RETRIABLE_STATUS_CODES:
                    error = "A retriable HTTP error %d occurred:\n%s" % (e.resp.status, e.content)
                else:
                    raise
            except self.RETRIABLE_EXCEPTIONS as e:
                error = "A retriable error occurred: %s" % e

            if error is not None:
                self.logger.info(error)
                retry += 1
                if retry > self.MAX_RETRIES:
                    self.logger.error("No longer attempting to retry.")
                    exit(code=-1)

                max_sleep = 2 ** retry
                sleep_seconds = random.random() * max_sleep
                self.logger.info("Sleeping %f seconds and then retrying..." % sleep_seconds)
                time.sleep(sleep_seconds)

        return response['id']


def setup_logger(name, logfile=f"./test.log"):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # -----

    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    handler_formatter = logging.Formatter("%(asctime)s|%(levelname)s|%(filename)s|%(message)s")
    handler.setFormatter(handler_formatter)
    logger.addHandler(handler)

    # -----

    rotate_handler = TimedRotatingFileHandler(logfile, when='midnight', interval=1, backupCount=7)
    rotate_handler.setLevel(logging.DEBUG)
    rotate_handler_formatter = logging.Formatter("%(asctime)s|%(levelname)s|%(filename)s|%(message)s")
    rotate_handler.setFormatter(rotate_handler_formatter)
    logger.addHandler(rotate_handler)

    return logger


if __name__ == '__main__':
    http.client.HTTPConnection.debuglevel=1
    # Explicitly tell the underlying HTTP transport library not to retry, since
    # we are handling retry logic ourselves.
    httplib2.RETRIES = 1
    VALID_PRIVACY_STATUSES = ("public", "private", "unlisted")

    logger = setup_logger(__name__, 'youtube.log')

    argparser = argparse.ArgumentParser(description='Video Upload')
    argparser.add_argument("--proc", required=True, help="proc file to upload")
    argparser.add_argument("--mp4", required=True, help="mp4 Video file to upload")

    argparser.add_argument("--title", help="Video title", default="Test Title")
    argparser.add_argument("--description", help="Video description", default="Test Description")
    argparser.add_argument("--category", default="27",
                           help="Numeric video category. See https://developers.google.com/youtube/v3/docs/videoCategories/list")
    argparser.add_argument("--keywords", help="Video keywords, comma separated", default="地震,jishin,earthquake")
    argparser.add_argument("--privacyStatus", choices=VALID_PRIVACY_STATUSES,
                           default=VALID_PRIVACY_STATUSES[2], help="Video privacy status.")

    args = argparser.parse_args()

    proc = Path(args.proc)
    if not proc.exists:
        logger.error("Please specify a valid file using the --proc= parameter.")
        exit(code=-1)

    mp4 = Path(args.mp4)
    if not mp4.exists():
        logger.error("Please specify a valid file using the --mp4= parameter.")
        exit(code=-1)

    proccessText = proc.read_bytes().decode('utf-16').splitlines()
    line = proccessText[0]
    lines = proccessText[1:]
    
    args.title = line
    args.description = '\n'.join(lines)

    logger.info(args.title)
    logger.info(args.description)
    # -------------
    
    try:
        yup = YoutubeUpload()
        yup.get_authenticated_service()
        upload_id = yup.initialize_upload(args)

        youtubepath = mp4.with_suffix('.mp4.youtube')
        youtubepath.write_text(upload_id, encoding='UTF-8')

    except HttpError as e:
        logger.error("An HTTP error %d occurred:\n%s" % (e.resp.status, e.content))
