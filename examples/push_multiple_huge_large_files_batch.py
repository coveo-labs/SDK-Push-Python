#!/usr/bin/env python
#-------------------------------------------------------------------------------------
# Push documents using the Start/End Batch method
#-------------------------------------------------------------------------------------

import json
import re
import csv
import urllib
import sys
import time
import zlib
import base64
import requests
import datetime
# Needed for the import of the csv

from coveopush import CoveoPush
from coveopush import Document
from coveopush import CoveoPermissions
from coveopush import CoveoConstants

def createDoc(myfile, version):
    # Create a document
    mydoc = Document('file:///' + version + "/" +myfile)
    # Get the file and compress it
    mydoc.GetFileAndCompress(myfile)
    # Set Metadata
    mydoc.AddMetadata("connectortype", "CSV")
    authors = []
    authors.append("Coveo")
    authors.append("R&D")
    # rssauthors should be set as a multi-value field in your Coveo Cloud organization
    mydoc.AddMetadata("rssauthors", authors)
    mydoc.Title = "THIS IS A TEST"
    # Set permissions
    user_email = "wim@coveo.com"
    myperm = CoveoPermissions.PermissionIdentity(CoveoConstants.Constants.PermissionIdentityType.User, "", user_email)
    mydoc.SetAllowedAndDeniedPermissions([myperm], [], True)
    return mydoc

def main():
    sourceId = '--Enter your source id--'
    orgId = '--Enter your org id--'
    apiKey = '--Enter your API key--'
    updateSourceStatus = True
    deleteOlder = True
    # Setup the push client
    push = CoveoPush.Push(sourceId, orgId, apiKey)

    # Start the batch
    push.Start(updateSourceStatus, deleteOlder)

    # Set the maximum 
    push.SetSizeMaxRequest(150*1024*1024)

    # Add the documents, if the buffer is full it will be pushed
    push.Add(createDoc('testfiles\\Large1.pptx', '1'))
    push.Add(createDoc('testfiles\\Large2.pptx', '1'))
    push.Add(createDoc('testfiles\\Large3.pptx', '1'))
    push.Add(createDoc('testfiles\\Large4.pptx', '1'))
    push.Add(createDoc('testfiles\\Large5.pptx', '1'))
    push.Add(createDoc('testfiles\\Large1.pptx', '2'))
    push.Add(createDoc('testfiles\\Large2.pptx', '2'))
    push.Add(createDoc('testfiles\\Large3.pptx', '2'))
    push.Add(createDoc('testfiles\\Large4.pptx', '2'))
    push.Add(createDoc('testfiles\\Large5.pptx', '2'))

    # End the Push
    push.End(updateSourceStatus, deleteOlder)

    
if __name__ == '__main__':
    main()
