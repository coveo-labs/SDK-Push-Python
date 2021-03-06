#!/usr/bin/env python
# -------------------------------------------------------------------------------------
# Push Single document with Data property
# -------------------------------------------------------------------------------------
import os

from coveopush import CoveoPush
from coveopush import Document
from coveopush import CoveoPermissions
from coveopush import CoveoConstants


def main():
    sourceId = os.environ.get('PUSH_SOURCE_ID') or '--Enter your source id--'
    orgId = os.environ.get('PUSH_ORG_ID') or '--Enter your org id--'
    apiKey = os.environ.get('PUSH_API_KEY') or '--Enter your API key--'

    # Setup the push client
    push = CoveoPush.Push(sourceId, orgId, apiKey)
    # Get a first Ordering Id
    startOrderingId = push.CreateOrderingId()

    # Create a document
    mydoc = Document("https://myreference&id=TESTME")
    # Set plain text
    mydoc.SetData("ALL OF THESE WORDS ARE SEARCHABLE")
    # Set FileExtension
    mydoc.FileExtension = ".html"
    # Add Metadata
    mydoc.AddMetadata("connectortype", "CSV")
    authors = []
    authors.append("Coveo")
    authors.append("R&D")
    # rssauthors should be set as a multi-value field in your Coveo Cloud organization
    mydoc.AddMetadata("rssauthors", authors)
    # Set the Title
    mydoc.Title = "THIS IS A TEST"
    # Set permissions
    user_email = "wim@coveo.com"
    # Create a permission identity
    myperm = CoveoPermissions.PermissionIdentity(CoveoConstants.Constants.PermissionIdentityType.User, "", user_email)
    # Set the permissions on the document
    allowAnonymous = True
    mydoc.SetAllowedAndDeniedPermissions([myperm], [], allowAnonymous)

    # Push the document
    push.AddSingleDocument(mydoc)

    # Delete older documents
    push.DeleteOlderThan(startOrderingId)


if __name__ == '__main__':
    main()
