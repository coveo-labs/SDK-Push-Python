#-------------------------------------------------------------------------------------
# CoveoConstants
#-------------------------------------------------------------------------------------
# Contains the Constants used by the SDK
#-------------------------------------------------------------------------------------
from enum import Enum

#---------------------------------------------------------------------------------
class LargeFileContainer:
  """Class to store the properties returned by LargeFile Container call """
  #The secure URI used to upload the item data into an Amazon S3 file.
  UploadUri = ''

  #The file identifier used to link the uploaded data to the pushed item.
  #This value needs to be set in the item 'CompressedBinaryDataFileId' metadata.
  FileId = ''

  #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
  #Default constructor used by the deserialization.
  def __init__(self, p_JSON):
    self.UploadUri = p_JSON['uploadUri']
    self.FileId = p_JSON['fileId']


#---------------------------------------------------------------------------------
class Constants:
  """Constants used within the Push Classes """
  # The default request timeout in seconds.
  DEFAULT_REQUEST_TIMEOUT_IN_SECONDS = 100

  # The default date format used by the Push API.
  DATE_FORMAT_STRING = "yyyy-MM-dd HH:mm:ss"

  # The date format used by the Activities service of the Platform API.
  DATE_WITH_MILLISECONDS_FORMAT_STRING = "yyyy-MM-ddTHH:mm:ss.fffZ"

  #The name of the default 'Email' security provider provisioned with each organization.
  EMAIL_SECURITY_PROVIDER_NAME = "Email Security Provider"

  #Max size (in bytes) of a document after being compressed-encoded.
  COMPRESSED_DATA_MAX_SIZE_IN_BYTES = 5*1024*1024

  #Max size (in bytes) of a request.
  #Limit in the Push API consumer is 256MB. --> was to big, we use 250 to be safe
  #32 bytes is removed from it to account for the JSON body structure.
  MAXIMUM_REQUEST_SIZE_IN_BYTES = 250*1024*1024 - 32

  #Reserved key names (case-insensitive) used in the Push API.
  s_DocumentReservedKeys = [
      "author",
      "clickableUri",
      "compressedBinaryData",
      "compressedBinaryDataFileId",
      "compressionType",
      "data",
      "date",
      "documentId",
      "fileExtension",
      "indexedDate",
      "parentId",
      "permissions",
      "orderingId"
  ]

  #---------------------------------------------------------------------------------
  class SourceStatusType(Enum):
    Rebuild = "REBUILD"
    Refresh = "REFRESH"
    Incremental = "INCREMENTAL"
    Idle = "IDLE"

  #---------------------------------------------------------------------------------
  class PermissionIdentityType(Enum):
    #Represents a standard, or undefined identity.
    Unknown = "UNKNOWN"

    #Represents a 'User' identity.
    User = "USER"

    #Represents a 'Group' identity.
    Group = "GROUP"

    #Represents a 'VirtualGroup' identity.
    VirtualGroup = "VIRTUAL_GROUP"

  #---------------------------------------------------------------------------------
  class CompressionType(Enum):
    UNCOMPRESSED = "UNCOMPRESSED"
    DEFLATE = "DEFLATE"
    GZIP = "GZIP"
    LZMA = "LZMA"
    ZLIB = "ZLIB"

  #---------------------------------------------------------------------------------
  class Retry:
    #The default number of retries when a request fails on a retryable error.
    DEFAULT_NUMBER_OF_RETRIES = 5

    #The default initial waiting time in milliseconds when a retry is performed.
    DEFAULT_INITIAL_WAITING_TIME_IN_MS = 2000

    #The maximum waiting time interval in milliseconds to add for each retry.
    DEFAULT_MAX_INTERVAL_TIME_TO_ADD_IN_MS = 2000

  #---------------------------------------------------------------------------------
  class PushVersion:
    VERSION = "v1"

  #---------------------------------------------------------------------------------
  class Endpoint:
    PROD_PUSH_API_URL = "https://push.cloud.coveo.com"
    HIPAA_PUSH_API_URL = "https://pushhipaa.cloud.coveo.com"
    QA_PUSH_API_URL = "https://pushqa.cloud.coveo.com"
    DEV_PUSH_API_URL = "https://pushdev.cloud.coveo.com"

  #---------------------------------------------------------------------------------
  class ErrorCodes:
    Codes = {}
    Codes["429"] = "Too many requests. Slow down your pushes! Are you using Batch Calls?"
    Codes["413"] = "Request too large. The document is too large to be processed. It should be under 5 mb."
    Codes["412"] = "Invalid or missing parameter - invalid source id"
    Codes["403"] = "Access Denied. Validate that your API Key has the proper access and that your Org and Source Id are properly specified"
    Codes["401"] = "Unauthorized or invalid token. Ensure your API key has the appropriate permissions."
    Codes["400"] = "Organization is Paused. Reactivate it OR Invalid JSON"
    Codes["504"] = "Timeout"

  #---------------------------------------------------------------------------------
  class PlatformEndpoint:
    PROD_PLATFORM_API_URL = "https://platform.cloud.coveo.com"
    HIPAA_PLATFORM_API_URL = "https://platformhipaa.cloud.com"
    QA_PLATFORM_API_URL = "https://platformqa.cloud.coveo.com"
    DEV_PLATFORM_API_URL = "https://platformdev.cloud.coveo.com"

  #---------------------------------------------------------------------------------
  class PushApiPaths:
    SOURCE_ACTIVITY_STATUS = "{version}/organizations/{org_id}/sources/{src_id}/status"
    SOURCE_DOCUMENTS = "{version}/organizations/{org_id}/sources/{src_id}/documents"
    SOURCE_DOCUMENTS_BATCH = "{version}/organizations/{org_id}/sources/{src_id}/documents/batch"
    SOURCE_DOCUMENTS_DELETE = "{version}/organizations/{org_id}/sources/{src_id}/documents/olderthan"
    DOCUMENT_GET_CONTAINER = "{version}/organizations/{org_id}/files"
    PROVIDER_PERMISSIONS = "{version}/organizations/{org_id}/providers/{prov_id}/permissions"
    PROVIDER_PERMISSIONS_DELETE = "{version}/organizations/{org_id}/providers/{prov_id}/permissions/olderthan"
    PROVIDER_PERMISSIONS_BATCH = "{version}/organizations/{org_id}/providers/{prov_id}/permissions/batch"
    PROVIDER_MAPPINGS = "{version}/organizations/{org_id}/providers/{prov_id}/mappings"
    CREATE_PROVIDER = "rest/organizations/{org_id}/securityproviders/{name_id}"

  #---------------------------------------------------------------------------------
  class Parameters:
    STATUS_TYPE = "statusType"
    FILE_ID = "fileId"
    ORDERING_ID = "orderingId"
    DOCUMENT_ID = "documentId"
    QUEUE_DELAY = "queueDelay"
    DELETE_CHILDREN = "deleteChildren"
    COMPRESSION_TYPE = "compressionType"

  #---------------------------------------------------------------------------------
  class HttpHeaders:
    AMAZON_S3_SERVER_SIDE_ENCRYPTION_NAME = "x-amz-server-side-encryption"
    AMAZON_S3_SERVER_SIDE_ENCRYPTION_VALUE = "AES256"
