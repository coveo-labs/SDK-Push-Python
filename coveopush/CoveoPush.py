# -------------------------------------------------------------------------------------
# CoveoPush
# -------------------------------------------------------------------------------------
# Contains the CoveoPush class
#   Can push documents, update securities
# -------------------------------------------------------------------------------------
from .CoveoConstants import Constants
from .CoveoDocument import Validate
from .CoveoDocument import Document
from .CoveoDocument import DocumentToDelete
from .CoveoDocument import BatchDocument
from .CoveoPermissions import PermissionIdentityExpansion
from .CoveoPermissions import PermissionIdentityBody
from .CoveoPermissions import BatchPermissions
from .CoveoPermissions import SecurityProvider
from .CoveoPermissions import SecurityProviderReference

import base64
import json
import jsonpickle
import logging
import re
import requests
import time


def Error(log, err):
    log.logger.info(err)
    raise Exception(err)


def isBase64(s):
    """
    isBase64.
    Checks if string is base64 encoded.
    Returns True/False
    """
    try:
        return base64.b64encode(base64.b64decode(s)) == s
    except Exception:
        return False


class LargeFileContainer:
    """Class to store the properties returned by LargeFile Container call """
    # The secure URI used to upload the item data into an Amazon S3 file.
    UploadUri = ''

    # The file identifier used to link the uploaded data to the pushed item.
    # This value needs to be set in the item 'CompressedBinaryDataFileId' metadata.
    FileId = ''

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Default constructor used by the deserialization.
    def __init__(self, p_JSON):
        self.UploadUri = p_JSON['uploadUri']
        self.FileId = p_JSON['fileId']


class Push:
    """
    class Push.
    Holds all methods to start pushing data.

    3 methods of pushing data:
    A) Push a single document
       Usage: When you simply need push a single document once in a while
       NOT TO BE USED: When you need to update a lot of documents. Use Method C or Method B for that.

        push = CoveoPush.Push( sourceId, orgId, apiKey)
        mydoc = CoveoDocument('https://myreference&id=TESTME')
        mydoc.SetData( "ALL OF THESE WORDS ARE SEARCHABLE")
        mydoc.FileExtension = ".html"
        mydoc.AddMetadata("connectortype", "CSV")
        mydoc.Title = "THIS IS A TEST"
        user_email = "wim@coveo.com"
        myperm = CoveoPermissions.PermissionIdentity(Constants.PermissionIdentityType.User, "", user_email )
        allowAnonymous = True
        mydoc.SetAllowedAndDeniedPermissions([myperm], [], allowAnonymous)
        push.AddSingleDocument(mydoc)

    B) Push a batch of documents in a single call
       Usage: When you need to upload a lot of (smaller) documents
       NOT TO BE USED: When you need to update a lot of LARGE documents. Use Method C for that.

        push = CoveoPush.Push( sourceId, orgId, apiKey)
        batch=[]
        batch.append(createDoc('testfiles\\BigExample.pdf'))
        batch.append(createDoc('testfiles\\BigExample2.pptx'))
        push.AddDocuments( batch, [], updateSourceStatus, deleteOlder)

    C) RECOMMENDED APPROACH: Push a batch of documents, document by document
       Usage: When you need to upload a lot of smaller/and or larger documents
       NOT TO BE USED: When you have a single document. Use Method A for that.

        push = CoveoPush.Push( sourceId, orgId, apiKey)
        push.Start( updateSourceStatus, deleteOlder)
        push.SetSizeMaxRequest( 150*1024*1024 )
        push.Add(createDoc('testfiles\\Large1.pptx','1'))
        push.Add(createDoc('testfiles\\Large2.pptx','1'))
        push.Add(createDoc('testfiles\\Large3.pptx','1'))
        push.Add(createDoc('testfiles\\Large4.pptx','1'))
        push.Add(createDoc('testfiles\\Large5.pptx','1'))
        push.Add(createDoc('testfiles\\Large1.pptx','2'))
        push.Add(createDoc('testfiles\\Large2.pptx','2'))
        push.Add(createDoc('testfiles\\Large3.pptx','2'))
        push.Add(createDoc('testfiles\\Large4.pptx','2'))
        push.Add(createDoc('testfiles\\Large5.pptx','2'))
        push.End( updateSourceStatus, deleteOlder)

    """
    SourceId = ''
    OrganizationId = ''
    ApiKey = ''
    PushApiEndpoint = Constants.PushApiEndpoint
    ProcessingDelayInMinutes = 0
    StartOrderingId = 0
    totalSize = 0
    ToAdd = []
    ToDel = []
    BatchPermissions = []
    MaxRequestSize = 0

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Default constructor used by the deserialization.
    def __init__(self, p_SourceId: str, p_OrganizationId: str, p_ApiKey: str, p_Endpoint: Constants.PushApiEndpoint = Constants.PushApiEndpoint.PROD_PUSH_API_URL):
        """
        Push Constructor.
        :arg p_SourceId: Source Id to use
        :arg p_OrganizationId: Organization Id to use
        :arg p_ApiKey: API Key to use
        :arg p_Endpoint: Constants.PushApiEndpoint
        """
        self.SourceId = p_SourceId
        self.OrganizationId = p_OrganizationId
        self.ApiKey = p_ApiKey
        self.Endpoint = p_Endpoint
        self.MaxRequestSize = 255052544
        self.logger = logging.getLogger('CoveoPush')
        self.SetupLogging()

        # validate Api Key
        if not re.match(r'^\w{10}-\w{4}-\w{4}-\w{4}-\w{12}$', p_ApiKey):
            self.logger.error('Invalid Api Key format')
            Error(self, "Invalid Api Key format")

        self.logger.debug('\n\n')
        self.logger.debug('------------------------------')
        self.logger.info('Pushing to source ' + self.SourceId)

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def SetSizeMaxRequest(self, p_Max: int):
        """
        SetSizeMaxRequest.
        By default MAXIMUM_REQUEST_SIZE_IN_BYTES is used (256 Mb)
        :arg p_Max: Max request size in bytes
        """
        if p_Max > Constants.MAXIMUM_REQUEST_SIZE_IN_BYTES:
            Error(self, "SetSizeMaxRequest: to big")

        self.MaxRequestSize = p_Max

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def GetSizeMaxRequest(self):
        if self.MaxRequestSize > 0:
            return self.MaxRequestSize

        return Constants.MAXIMUM_REQUEST_SIZE_IN_BYTES

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def SetupLogging(self, p_LEVEL=logging.DEBUG, p_OutputFile='CoveoPush.log', p_Format="%(asctime)s %(levelname)-5s [%(filename)s:%(lineno)s %(funcName)s()] %(message)s"):
        """
        SetupLogging.
        :arg p_LEVEL: Logging level (logging.DEBUG)
        :arg p_OutputFile: Log file to write (CoveoPush.log)
        :arg p_Format: Format of the log file ('%(asctime)s %(levelname)-5s [%(filename)s:%(lineno)s %(funcName)s()] %(message)s')
        """

        logging.basicConfig(filename=p_OutputFile, level=p_LEVEL, format=p_Format, datefmt='%Y-%m-%d %H:%M:%S')

        if p_LEVEL == logging.DEBUG:
            req_log = logging.getLogger('requests.packages.urllib3')
            req_log.setLevel(logging.DEBUG)
            req_log.propagate = True

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def GetRequestHeaders(self):
        """
        GetRequestHeaders.
        Gets the Request headers needed for every Push call.
        """

        self.logger.debug('GetRequestHeaders')
        return {
            'Authorization': 'Bearer ' + self.ApiKey,
            'content-type': 'application/json'
        }

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def GetRequestHeadersForS3(self):
        """
        GetRequestHeadersForS3.
        Gets the Request headers needed for calls to Amazon S3.
        """

        return {
            'Content-Type': 'application/octet-stream',
            Constants.HttpHeaders.AMAZON_S3_SERVER_SIDE_ENCRYPTION_NAME: Constants.HttpHeaders.AMAZON_S3_SERVER_SIDE_ENCRYPTION_VALUE
        }

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def GetStatusUrl(self):
        """
        GetStatusUrl.
        Get the URL to update the Status of the source call
        """

        url = Constants.PushApiPaths.SOURCE_ACTIVITY_STATUS.format(
            endpoint=self.Endpoint,
            org_id=self.OrganizationId,
            src_id=self.SourceId
        )
        self.logger.debug(url)
        return url

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def CreateOrderingId(self):
        """
        CreateOrderingId.
        Create an Ordering Id, used to set the order of the pushed items
        """

        ordering_id = int(round(time.time() * 1000))
        self.logger.debug(ordering_id)
        return ordering_id

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def GetLargeFileContainerUrl(self):
        """
        GetLargeFileContainerUrl.
        Get the URL for the Large File Container call.
        """

        url = Constants.PushApiPaths.DOCUMENT_GET_CONTAINER.format(
            endpoint=self.Endpoint,
            org_id=self.OrganizationId
        )
        self.logger.debug(url)
        return url

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def GetUpdateDocumentUrl(self):
        """
        GetUpdateDocumentUrl.
        Get the URL for the Update Document call.
        """

        url = Constants.PushApiPaths.SOURCE_DOCUMENTS.format(
            endpoint=self.Endpoint,
            org_id=self.OrganizationId,
            src_id=self.SourceId
        )
        self.logger.debug(url)
        return url

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def GetSecurityProviderUrl(self, p_Endpoint: str, p_SecurityProviderId: str):
        """
        GetSecurityProviderUrl.
        Get the URL to create the security provider
        """

        url = Constants.PlatformPaths.CREATE_PROVIDER.format(
            endpoint=p_Endpoint,
            org_id=self.OrganizationId,
            prov_id=p_SecurityProviderId
        )
        self.logger.debug(url)
        return url

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def GetDeleteDocumentUrl(self):
        """
        GetDeleteDocumentUrl.
        Get the URL for the Delete Document call.
        """

        url = Constants.PushApiPaths.SOURCE_DOCUMENTS.format(
            endpoint=self.Endpoint,
            org_id=self.OrganizationId,
            src_id=self.SourceId
        )
        self.logger.debug(url)
        return url

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def GetUpdateDocumentsUrl(self):
        """
        GetUpdateDocumentsUrl.
        Get the URL for the Update Documents (batch) call.
        """

        url = Constants.PushApiPaths.SOURCE_DOCUMENTS_BATCH.format(
            endpoint=self.Endpoint,
            org_id=self.OrganizationId,
            src_id=self.SourceId
        )
        self.logger.debug(url)
        return url

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def GetDeleteOlderThanUrl(self):
        """
        GetDeleteOlderThanUrl.
        Get the URL for the Delete Older Than call.
        """

        url = Constants.PushApiPaths.SOURCE_DOCUMENTS_DELETE.format(
            endpoint=self.Endpoint,
            org_id=self.OrganizationId,
            src_id=self.SourceId
        )
        self.logger.debug(url)
        return url

    def GetUrl(self, path, prov_id: str = ''):
        """
        Return path with values (endpoint, org, source, provider) set accordingly.
        """
        url = path.format(
            endpoint=self.Endpoint,
            org_id=self.OrganizationId,
            src_id=self.SourceId,
            prov_id=prov_id
        )
        self.logger.debug(url)
        return url

    def CheckReturnCode(self, p_Response):
        """
        CheckReturnCode.
        Checks the return code of the response (from the request object).
        If not valid an error will be raised.
        :arg p_Response: response from request
        """
        self.logger.debug(p_Response.status_code)
        if p_Response.status_code == 403:
            self.logger.error('Check privileges on your Api key.')

        if p_Response.status_code >= 300:
            self.logger.error(p_Response.text)

        p_Response.raise_for_status()

        return p_Response.status_code

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def UpdateSourceStatus(self, p_SourceStatus: Constants.SourceStatusType):
        """
        UpdateSourceStatus.
        Update the Source status, so that the activity on the source reflects what is going on
        :arg p_SourceStatus: Constants.SourceStatusType (REBUILD, IDLE)
        """

        self.logger.info('Changing status to ' + p_SourceStatus.value)
        params = {
            Constants.Parameters.STATUS_TYPE: p_SourceStatus.value
        }

        # make POST request to change status
        r = requests.post(
            self.GetStatusUrl(),
            headers=self.GetRequestHeaders(),
            params=params
        )
        return self.CheckReturnCode(r)

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def GetLargeFileContainer(self):
        """
        GetLargeFileContainer.
        Get the S3 Large Container information.
        returns: LargeFileContainer Class
        """

        self.logger.debug(self.GetLargeFileContainerUrl())
        r = requests.post(
            self.GetLargeFileContainerUrl(),
            headers=self.GetRequestHeaders()
        )
        self.CheckReturnCode(r)

        results = LargeFileContainer(json.loads(r.text))
        return results

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def UploadDocument(self, p_UploadUri: str, p_CompressedFile: str):
        """
        UploadDocument.
        Upload a document to S3.
        :arg p_UploadUri: string, retrieved from the GetLargeFileContainer call
        :arg p_CompressedFile: string, Properly compressed file to upload as contents
        """

        self.logger.debug(p_UploadUri)

        if not p_UploadUri:
            Error(self, "UploadDocument: p_UploadUri is not present")
        if not p_CompressedFile:
            Error(self, "UploadDocument: p_CompressedFile is not present")

        # Check if p_CompressedFile is base64 encoded, if so, decode it first
        if (isBase64(p_CompressedFile)):
            p_CompressedFile = base64.b64decode(p_CompressedFile)

        r = requests.put(
            p_UploadUri,
            data=p_CompressedFile,
            headers=self.GetRequestHeadersForS3()
        )
        self.CheckReturnCode(r)
        self.logger.debug('result: '+str(r.status_code))

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def UploadDocuments(self, p_UploadUri: str, p_ToAdd: [], p_ToDelete: []):
        """
        UploadDocuments.
        Upload a batch document to S3.
        :arg p_UploadUri: string, retrieved from the GetLargeFileContainer call
        :arg p_ToAdd: list of CoveoDocuments to add
        :arg p_ToDelete: list of CoveoDocumentToDelete to delete
        """

        self.logger.debug(p_UploadUri)

        if not p_UploadUri:
            Error(self, "UploadDocument: p_UploadUri is not present")
        if not p_ToAdd and not p_ToDelete:
            Error(self, "UploadBatch: p_ToAdd and p_ToDelete are empty")

        data = BatchDocument()
        data.AddOrUpdate = p_ToAdd
        data.Delete = p_ToDelete

        r = requests.put(
            p_UploadUri,
            data=jsonpickle.encode(data, unpicklable=False),
            headers=self.GetRequestHeadersForS3()
        )
        self.CheckReturnCode(r)
        self.logger.debug('result: '+str(r.status_code))

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def UploadPermissions(self, p_UploadUri: str):
        """
        UploadPermissions.
        Upload a batch permission to S3.
        :arg p_UploadUri: string, retrieved from the GetLargeFileContainer call
        """

        self.logger.debug(p_UploadUri)

        if not p_UploadUri:
            Error(self, "UploadPermissions: p_UploadUri is not present")

        pickled_permissions = jsonpickle.encode(self.BatchPermissions, unpicklable=False)
        self.logger.debug("JSON: " + pickled_permissions)

        r = requests.put(
            p_UploadUri,
            data=pickled_permissions,
            headers=self.GetRequestHeadersForS3()
        )

        self.CheckReturnCode(r)
        self.logger.debug('result: '+str(r.status_code))

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def GetContainerAndUploadDocument(self, p_Content: str):
        """
        GetContainerAndUploadDocument.
        Get a Large File Container instance and Upload the document to S3
        :arg p_Content: string, Properly compressed file to upload as contents
        return: S3 FileId value
        """

        self.logger.debug('GetContainerAndUploadDocument')
        container = self.GetLargeFileContainer()
        if not container:
            Error(self, "GetContainerAndUploadDocument: S3 container is null")

        self.UploadDocument(container.UploadUri, p_Content)

        return container.FileId

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def UploadDocumentIfTooLarge(self, p_Document: Document):
        """
        UploadDocumentIfTooLarge.
        Uploads an Uncompressed/Compressed Document, if it is to large a S3 container is created, document is being uploaded to s3
        :arg p_Document: Document
        """

        size = len(p_Document.Data)+len(p_Document.CompressedBinaryData)
        self.logger.debug('size = ' + str(size))

        if (size > Constants.COMPRESSED_DATA_MAX_SIZE_IN_BYTES):
            data = ''
            if p_Document.Data:
                data = p_Document.Data
            else:
                data = p_Document.CompressedBinaryData

            fileId = self.GetContainerAndUploadDocument(data)
            p_Document.SetCompressedDataFileId(fileId)

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def AddUpdateDocumentRequest(self, p_CoveoDocument: Document, orderingId: int = None):
        """
        AddUpdateDocumentRequest.
        Sends the document to the Push API, if previously uploaded to s3 the fileId is set
        :arg p_Document: Document
        :arg orderingId: int (optional)
        """

        params = {
            Constants.Parameters.DOCUMENT_ID: p_CoveoDocument.DocumentId
        }

        if orderingId is not None:
            params[Constants.Parameters.ORDERING_ID] = orderingId

        self.logger.debug(params)

        # Set the compression type parameter
        if (p_CoveoDocument.CompressedBinaryData != '' or p_CoveoDocument.CompressedBinaryDataFileId != ''):
            params[Constants.Parameters.COMPRESSION_TYPE] = p_CoveoDocument.CompressionType

        body = jsonpickle.encode(p_CoveoDocument.ToJson(), unpicklable=False)
        # self.logger.debug(body)

        # make POST request to change status
        r = requests.put(
            self.GetUpdateDocumentUrl(),
            data=body,
            headers=self.GetRequestHeaders(),
            params=params
        )
        self.CheckReturnCode(r)
        return r.status_code

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def DeleteDocument(self, p_DocumentId: str, orderingId: int = None, deleteChildren: bool = False):
        """
        Deletes the document
        :arg p_DocumentId: CoveoDocument
        :arg orderingId: int
        :arg deleteChildren: bool, if children must be deleted
        """

        params = {
            Constants.Parameters.DOCUMENT_ID: p_DocumentId
        }

        if orderingId is not None:
            params[Constants.Parameters.ORDERING_ID] = orderingId

        if deleteChildren:
            params[Constants.Parameters.DELETE_CHILDREN] = deleteChildren

        self.logger.debug(params)

        # delete it
        r = requests.delete(
            self.GetDeleteDocumentUrl(),
            headers=self.GetRequestHeaders(),
            params=params
        )
        self.CheckReturnCode(r)
        return r.status_code

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def DeleteOlderThan(self, orderingId: int = 0, queueDelay: int = None):
        """
        DeleteOlderThan.
        All documents with a smaller orderingId will be removed from the index
        :arg orderingId: int
        """

        self.logger.debug(f'orderingId: {orderingId}, queueDelay: {queueDelay}')
        # Validate
        if orderingId <= 0:
            Error(self, "DeleteOlderThan: orderingId must be a positive 64 bit integer.")

        params = {
            Constants.Parameters.ORDERING_ID: orderingId
        }

        if queueDelay is not None:
            if not (queueDelay >= 0 and queueDelay <= 1440):
                Error(self, "DeleteOlderThan: queueDelay must be between 0 and 1440.")
            else:
                params[Constants.Parameters.QUEUE_DELAY] = queueDelay

        r = requests.delete(
            self.GetDeleteOlderThanUrl(),
            headers=self.GetRequestHeaders(),
            params=params
        )
        self.CheckReturnCode(r)
        return r.status_code

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def AddSingleDocument(self, p_CoveoDocument: Document, updateStatus: bool = True, orderingId: int = None):
        """
        AddSingleDocument.
        Pushes the Document to the Push API
        :arg p_CoveoDocument: Document
        :arg p_UpdateStatus: bool (True), if the source status should be updated
        :arg orderingId: int, optional
        """

        self.logger.info(p_CoveoDocument.DocumentId)
        # Single Call
        # First check
        valid, error = Validate(p_CoveoDocument)
        if not valid:
            Error(self, "AddSingleDocument: "+error)

        # Update Source Status
        if updateStatus:
            self.UpdateSourceStatus(Constants.SourceStatusType.Rebuild)

        # Push Document
        try:
            if (p_CoveoDocument.CompressedBinaryData != '' or p_CoveoDocument.Data != ''):
                self.UploadDocumentIfTooLarge(p_CoveoDocument)
            self.AddUpdateDocumentRequest(p_CoveoDocument, orderingId)
        finally:
            p_CoveoDocument.Content = ''

        # Update Source Status
        if updateStatus:
            self.UpdateSourceStatus(Constants.SourceStatusType.Idle)

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def RemoveSingleDocument(self, p_DocumentId: str, updateStatus: bool = True, orderingId: int = None, deleteChildren: bool = False):
        """
        RemoveSingleDocument.
        Deletes the CoveoDocument to the Push API
        :arg p_DocumentId: str of the document to delete
        :arg updateStatus: bool (True), if the source status should be updated
        :arg orderingId: int, if not supplied a new one will be created
        :arg deleteChildren: bool (False), if children must be deleted
        """

        # Single Call

        # Update Source Status
        if updateStatus:
            self.UpdateSourceStatus(Constants.SourceStatusType.Rebuild)

        # Delete document
        self.DeleteDocument(p_DocumentId, orderingId, deleteChildren)

        # Update Source Status
        if updateStatus:
            self.UpdateSourceStatus(Constants.SourceStatusType.Idle)

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def AddUpdateDocumentsRequest(self, p_FileId: str):
        """
        AddUpdateDocumentsRequest.
        Sends the documents to the Push API, if previously uploaded to s3 the fileId is set
        :arg p_FileId: File Id retrieved from GetLargeFileContainer call
        """

        self.logger.debug(p_FileId)
        params = {
            Constants.Parameters.FILE_ID: p_FileId
        }
        # make POST request to change status
        r = requests.put(
            self.GetUpdateDocumentsUrl(),
            headers=self.GetRequestHeaders(),
            params=params
        )
        self.CheckReturnCode(r)
        return r.status_code

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def UploadBatch(self, p_ToAdd: [], p_ToDelete: []):
        """
        UploadBatch.
        Uploads the batch to S3 and calls the Push API to record the fileId
        :arg p_ToAdd: list of CoveoDocuments to add
        :arg p_ToDelete: list of CoveoDocumentToDelete to delete
        """

        self.logger.debug('UploadBatch')
        if not p_ToAdd and not p_ToDelete:
            Error(self, "UploadBatch: p_ToAdd and p_ToDelete are empty")

        container = self.GetLargeFileContainer()
        if not container:
            Error(self, "UploadBatch: S3 container is null")

        self.UploadDocuments(container.UploadUri, p_ToAdd, p_ToDelete)
        self.AddUpdateDocumentsRequest(container.FileId)

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def ProcessAndUploadBatch(self, p_Documents: []):
        """
        ProcessAndUploadBatch.
        Will create batches of documents to push to S3 and to upload to the Push API
        :arg p_Documents: list of CoveoDocument/CoveoDocumentToDelete to add/delete
        """

        self.logger.debug('ProcessAndUploadBatch')
        currentBatchToDelete = []
        currentBatchToAddUpdate = []

        totalSize = 0
        for document in p_Documents:
            # Add 1 byte to account for the comma in the JSON array.
            # documentSize = len(json.dumps(document,default=lambda x: x.__dict__)) + 1
            documentSize = len(jsonpickle.encode(document.ToJson(), unpicklable=False)) + 1

            totalSize += documentSize
            self.logger.debug("Doc: "+document.DocumentId)
            self.logger.debug("Currentsize: "+str(totalSize) + " vs max: "+str(self.GetSizeMaxRequest()))

            if (documentSize > self.GetSizeMaxRequest()):
                Error(self, "No document can be larger than " + str(self.GetSizeMaxRequest())+" bytes in size.")

            if (totalSize > self.GetSizeMaxRequest() - (len(currentBatchToAddUpdate) + len(currentBatchToDelete))):
                self.UploadBatch(currentBatchToAddUpdate, currentBatchToDelete)
                currentBatchToAddUpdate = []
                currentBatchToDelete = []
                totalSize = documentSize

            if (type(document) is DocumentToDelete):
                currentBatchToDelete.append(document.ToJson())
            else:
                # Validate each document
                valid, error = Validate(document)
                if not valid:
                    Error(self, "PushDocument: " + document.DocumentId + ", " + error)
                else:
                    currentBatchToAddUpdate.append(document.ToJson())

        self.UploadBatch(currentBatchToAddUpdate, currentBatchToDelete)

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def AddDocuments(self, p_CoveoDocumentsToAdd: [], p_CoveoDocumentsToDelete: [], p_UpdateStatus: bool = True, p_DeleteOlder: bool = False):
        """
        AddDocuments.
        Adds all documents in several batches to the Push API.
        :arg p_CoveoDocumentsToAdd: list of CoveoDocument to add
        :arg p_CoveoDocumentsToDelete: list of CoveoDocumentToDelete
        :arg p_UpdateStatus: bool (True), if the source status should be updated
        :arg p_DeleteOlder: bool (False), if older documents should be removed from the index after the new push
        """

        self.logger.debug('AddDocuments')
        # Batch Call
        # First check
        StartOrderingId = self.CreateOrderingId()

        if not p_CoveoDocumentsToAdd and not p_CoveoDocumentsToDelete:
            Error(self, "AddDocuments: p_CoveoDocumentsToAdd and p_CoveoDocumentsToDelete is empty")

        # Update Source Status
        if p_UpdateStatus:
            self.UpdateSourceStatus(Constants.SourceStatusType.Rebuild)

        # Push the Documents
        if p_CoveoDocumentsToAdd:
            allDocuments = p_CoveoDocumentsToAdd

        if p_CoveoDocumentsToDelete:
            allDocuments = allDocuments.extend(p_CoveoDocumentsToDelete)

        self.ProcessAndUploadBatch(allDocuments)

        # Delete Older Documents
        if p_DeleteOlder:
            self.DeleteOlderThan(StartOrderingId)

        # Update Source Status
        if p_UpdateStatus:
            self.UpdateSourceStatus(Constants.SourceStatusType.Idle)

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def Start(self, p_UpdateStatus: bool = True):
        """
        Start.
        Starts a batch Push call, will set the start ordering Id and will update the status of the source
        :arg p_UpdateStatus: bool (True), if the source status should be updated
        """

        self.logger.debug('Start')
        # Batch Call
        # First check
        self.StartOrderingId = self.CreateOrderingId()

        # Update Source Status
        if p_UpdateStatus:
            self.UpdateSourceStatus(Constants.SourceStatusType.Rebuild)

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def Add(self, p_CoveoDocument):
        """
        Add.
        Add a document to the batch call, if the buffer max is reached content is pushed
        :arg p_CoveoDocument: Coveoocument of CoveoDocumentToDelete
        """

        self.logger.debug('Add')

        if not p_CoveoDocument:
            Error(self, "Add: p_CoveoDocument is empty")

        documentSize = len(jsonpickle.encode(p_CoveoDocument.ToJson(), unpicklable=False)) + 1

        self.totalSize += documentSize
        self.logger.debug("Doc: "+p_CoveoDocument.DocumentId)
        self.logger.debug("Currentsize: "+str(self.totalSize) + " vs max: "+str(self.GetSizeMaxRequest()))

        if (documentSize > self.GetSizeMaxRequest()):
            Error(self, "No document can be larger than " + str(self.GetSizeMaxRequest())+" bytes in size.")

        if (self.totalSize > self.GetSizeMaxRequest() - (len(self.ToAdd) + len(self.ToDel))):
            self.UploadBatch(self.ToAdd, self.ToDel)
            self.ToAdd = []
            self.ToDel = []
            self.totalSize = documentSize

        if (type(p_CoveoDocument) is DocumentToDelete):
            self.ToDel.append(p_CoveoDocument.ToJson())
        else:
            # Validate each document
            valid, error = Validate(p_CoveoDocument)
            if not valid:
                Error(self, "Add: "+p_CoveoDocument.DocumentId+", "+error)
            else:
                self.ToAdd.append(p_CoveoDocument.ToJson())

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def End(self, p_UpdateStatus: bool = True, p_DeleteOlder: bool = False):
        """
        End.
        Ends the batch call (when started with Start()). Will push the final batch, update the status and delete older documents
        :arg p_UpdateStatus: bool (True), if the source status should be updated
        :arg p_DeleteOlder: bool (False), if older documents should be removed from the index after the new push
        """

        self.logger.debug('End')
        # Batch Call
        self.UploadBatch(self.ToAdd, self.ToDel)

        # Delete Older Documents
        if p_DeleteOlder:
            self.DeleteOlderThan(self.StartOrderingId)

        self.ToAdd = []
        self.ToDel = []

        # Update Source Status
        if p_UpdateStatus:
            self.UpdateSourceStatus(Constants.SourceStatusType.Idle)

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def AddSecurityProvider(self, p_SecurityProviderId: str, p_Type: str, p_CascadingTo: {}, p_Endpoint: Constants.PlatformEndpoint = Constants.PlatformEndpoint.PROD_PLATFORM_API_URL):
        """
        AddSecurityProvider.
        Add a single Permission Expansion (PermissionIdentityBody)
        :arg p_SecurityProviderId: Security Provider name and Id to use
        :arg p_Type: Type of provider, normally 'EXPANDED'
        :arg p_CascadingTo: dictionary
        :arg p_Endpoint: Constants.PlatformEndpoint
        """
        secProvider = SecurityProvider()
        secProviderReference = SecurityProviderReference(self.SourceId, "SOURCE")
        secProvider.referencedBy = [secProviderReference]
        secProvider.name = p_SecurityProviderId
        secProvider.type = p_Type
        secProvider.nodeRequired = False
        secProvider.cascadingSecurityProviders = p_CascadingTo

        self.logger.debug('AddSecurityProvider')

        # make POST request to change status
        pickled_provider = jsonpickle.encode(secProvider, unpicklable=False)
        self.logger.debug("JSON: "+pickled_provider)
        r = requests.put(
            self.GetSecurityProviderUrl(p_Endpoint, p_SecurityProviderId),
            data=pickled_provider,
            headers=self.GetRequestHeaders()
        )
        self.CheckReturnCode(r)
        return r.status_code

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def AddPermissionExpansion(self, p_SecurityProviderId: str, p_Identity: PermissionIdentityExpansion, p_Members: [], p_Mappings: [], p_WellKnowns: [], orderingId: int = None):
        """
        AddPermissionExpansion.
        Add a single Permission Expansion Call (PermissionIdentityBody)
        :arg p_SecurityProviderId: Security Provider to use
        :arg p_Identity: PermissionIdentityExpansion.
        :arg p_Members: list of PermissionIdentityExpansion.
        :arg p_Mappings: list of PermissionIdentityExpansion.
        :arg p_WellKnowns: list of PermissionIdentityExpansion.
        :arg orderingId: orderingId. (optional)
        """
        self.logger.debug('AddPermissionExpansion')

        permissionIdentityBody = PermissionIdentityBody(p_Identity)
        permissionIdentityBody.AddMembers(p_Members)
        permissionIdentityBody.AddMappings(p_Mappings)
        permissionIdentityBody.AddWellKnowns(p_WellKnowns)

        params = {}

        if orderingId is not None:
            params[Constants.Parameters.ORDERING_ID] = orderingId

        resourcePathFormat = Constants.PushApiPaths.PROVIDER_PERMISSIONS
        if p_Mappings:
            resourcePathFormat = Constants.PushApiPaths.PROVIDER_MAPPINGS

        resourcePath = resourcePathFormat.format(
            endpoint=self.Endpoint,
            org_id=self.OrganizationId,
            prov_id=p_SecurityProviderId
        )

        pickled_identity = jsonpickle.encode(permissionIdentityBody, unpicklable=False)

        self.logger.debug(f'JSON: {pickled_identity}')

        # Update permission
        r = requests.put(
            resourcePath,
            data=pickled_identity,
            headers=self.GetRequestHeaders(),
            params=params
        )
        self.CheckReturnCode(r)
        return r.status_code
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def StartExpansion(self, p_SecurityProviderId: str, p_DeleteOlder: bool = False):
        """
        StartExpansion.
        Will start a Batch for Expansion/Permission updates.
        Using AddExpansionMember, AddExpansionMapping or AddExpansionDeleted operations are added.
        EndExpansion must be called at the end to write the Batch to the Push API.
        :arg p_SecurityProviderId: Security Provider to use
        :arg p_DeleteOlder: bool (False), if older documents should be removed from the index after the new push
        """

        self.logger.debug('StartExpansion')
        # Batch Call
        # First check
        self.StartOrderingId = self.CreateOrderingId()
        self.BatchPermissions = BatchPermissions()

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def AddExpansionMember(self, p_Identity: PermissionIdentityExpansion, p_Members: [], p_Mappings: [], p_WellKnowns: []):
        """
        AddExpansionMember.
        For example: GROUP has 3 members.
        Add a single Permission Expansion (PermissionIdentityBody) to the Members
        :arg p_Identity: PermissionIdentityExpansion, must be the same as Identity in PermissionIdentity when pushing documents.
        :arg p_Members: list of PermissionIdentityExpansion.
        :arg p_Mappings: list of PermissionIdentityExpansion.
        :arg p_WellKnowns: list of PermissionIdentityExpansion.
        """
        self.logger.debug('AddExpansionMember')
        permissionIdentityBody = PermissionIdentityBody(p_Identity)
        permissionIdentityBody.AddMembers(p_Members)
        permissionIdentityBody.AddMappings(p_Mappings)
        permissionIdentityBody.AddWellKnowns(p_WellKnowns)
        self.BatchPermissions.AddMembers(permissionIdentityBody)

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def AddExpansionMapping(self, p_Identity: PermissionIdentityExpansion, p_Members: [], p_Mappings: [], p_WellKnowns: []):
        """
        AddExpansionMapping.
        For example: Identity WIM has 3 mappings: wim@coveo.com, w@coveo.com, ad\\w
        Add a single Permission Expansion (PermissionIdentityBody) to the Mappings
        :arg p_Identity: PermissionIdentityExpansion, must be the same as Identity in PermissionIdentity when pushing documents.
        :arg p_Members: list of PermissionIdentityExpansion.
        :arg p_Mappings: list of PermissionIdentityExpansion.
        :arg p_WellKnowns: list of PermissionIdentityExpansion.
        """
        self.logger.debug('AddExpansionMapping')
        permissionIdentityBody = PermissionIdentityBody(p_Identity)
        permissionIdentityBody.AddMembers(p_Members)
        permissionIdentityBody.AddMappings(p_Mappings)
        permissionIdentityBody.AddWellKnowns(p_WellKnowns)
        self.BatchPermissions.AddMappings(permissionIdentityBody)

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def AddExpansionDeleted(self, p_Identity: PermissionIdentityExpansion, p_Members: [], p_Mappings: [], p_WellKnowns: []):
        """
        AddExpansionDeleted.
        Add a single Permission Expansion (PermissionIdentityBody) to the Deleted, will be deleted from the security cache
        :arg p_Identity: PermissionIdentityExpansion, must be the same as Identity in PermissionIdentity when pushing documents.
        :arg p_Members: list of PermissionIdentityExpansion.
        :arg p_Mappings: list of PermissionIdentityExpansion.
        :arg p_WellKnowns: list of PermissionIdentityExpansion.
        """
        self.logger.debug('AddExpansionDeleted')
        permissionIdentityBody = PermissionIdentityBody(p_Identity)
        permissionIdentityBody.AddMembers(p_Members)
        permissionIdentityBody.AddMappings(p_Mappings)
        permissionIdentityBody.AddWellKnowns(p_WellKnowns)
        self.BatchPermissions.AddDeletes(permissionIdentityBody)

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def EndExpansion(self, p_SecurityProviderId: str, p_DeleteOlder: bool = False):
        """
        EndExpansion.
        Will write the last batch of security updates to the push api
        :arg p_SecurityProviderId: Security Provider to use
        :arg p_DeleteOlder: bool (False), if older documents should be removed from the index after the new push
        """
        self.logger.debug('EndExpansion')
        container = self.GetLargeFileContainer()
        if not container:
            Error(self, "UploadBatch: S3 container is null")

        self.UploadPermissions(container.UploadUri)
        params = {
            Constants.Parameters.FILE_ID: container.FileId
        }

        resourcePathFormat = Constants.PushApiPaths.PROVIDER_PERMISSIONS_BATCH
        resourcePath = resourcePathFormat.format(
            endpoint=self.Endpoint,
            org_id=self.OrganizationId,
            prov_id=p_SecurityProviderId
        )

        # Update permission
        r = requests.put(
            resourcePath,
            headers=self.GetRequestHeaders(),
            params=params
        )
        self.CheckReturnCode(r)

        if p_DeleteOlder:
            self.DeletePermissionsOlderThan(p_SecurityProviderId, self.StartOrderingId)

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def RemovePermissionIdentity(self, p_SecurityProviderId: str, p_PermissionIdentity: PermissionIdentityExpansion):
        """
        RemovePermissionIdentity.
        Remove a single Permission Mapping
        :arg p_SecurityProviderId: Security Provider to use
        :arg p_PermissionIdentity: PermissionIdentityExpansion, permissionIdentity to remove
        """
        self.logger.debug('RemovePermissionIdentity')
        permissionIdentityBody = PermissionIdentityBody(p_PermissionIdentity)
        resourcePathFormat = Constants.PushApiPaths.PROVIDER_PERMISSIONS
        resourcePath = resourcePathFormat.format(
            endpoint=self.Endpoint,
            org_id=self.OrganizationId,
            prov_id=p_SecurityProviderId
        )

        # Update permission
        pickled_identity = jsonpickle.encode(permissionIdentityBody, unpicklable=False)

        self.logger.debug("JSON: " + pickled_identity)

        r = requests.delete(
            resourcePath,
            data=pickled_identity,
            headers=self.GetRequestHeaders()
        )
        self.CheckReturnCode(r)
        return r.status_code

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def DeletePermissionsOlderThan(self, p_SecurityProviderId: str, orderingId: int = 0):
        """
        DeletePermissionOlderThan.
        Deletes permissions older than orderingId
        :arg p_SecurityProviderId: Security Provider to use
        :arg orderingId: int, the OrderingId to use
        """
        self.logger.debug('DeletePermissionsOlderThan')

        if orderingId <= 0:
            Error(self, "DeletePermissionsOlderThan: orderingId must be a positive 64 bit integer.")

        params = {
            Constants.Parameters.ORDERING_ID: orderingId
        }

        resourcePathFormat = Constants.PushApiPaths.PROVIDER_PERMISSIONS_DELETE
        resourcePath = resourcePathFormat.format(
            endpoint=self.Endpoint,
            org_id=self.OrganizationId,
            prov_id=p_SecurityProviderId
        )

        # Update permission
        r = requests.delete(
            resourcePath,
            headers=self.GetRequestHeaders(),
            params=params
        )
        self.CheckReturnCode(r)
        return r.status_code
