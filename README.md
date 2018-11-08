# Coveo Push API SDK for Python

The Coveo Push API SDK for Python is meant to help you use the [Coveo Push API](https://docs.coveo.com/en/68/cloud-v2-developers/push-api) when coding in Python.

This SDK includes the following features:

- Document validation before they are pushed to the plaform
- Source update status before and after a document update
- Automatic push of large files to the platform through an Amazon S3 container

For code examples on how to use the SDK, see the `examples` section.

## Installation

Make sure you have [git](https://git-scm.com/downloads) installed.

Then, in your command prompt, enter the following command:

```
pip install git+https://github.com/coveo-labs/SDK-Push-Python
```

This SDK depends on the [Python Requests](http://docs.python-requests.org/en/master/user/install/#install) and [JSONPickle](https://jsonpickle.github.io/#download-install) libraries. If you do not already have them, you need to run the following commands:

```
pip install requests
pip install jsonpickle
```

## Including the SDK in Your Code

Simply add the following lines into your project:

```python
from coveopush import CoveoPush
from coveopush import Document
from coveopush import CoveoPermissions
from coveopush import CoveoConstants
```

## Prerequisites

Before pushing a document to a Coveo Cloud organization, you need to ensure that you have a Coveo Cloud organization, and that this organization has a [Push source](https://docs.coveo.com/en/94/cloud-v2-developers/creating-a-push-source).

Once you have those prerequisites, you need to get your Organization Id, Source Id, and API Key. For more information on how to do that, see [Push API Tutorial 1 - Managing Shared Content](https://docs.coveo.com/en/92/cloud-v2-developers/push-api-tutorial-1---managing-shared-content).

You must also create fields and mappings for each metadata you will be sending with your documents. Otherwise, some of the data you push might get ignored by Coveo Cloud. To learn how to create fields and mappings in Coveo Cloud, see [Add/Edit a Field: [FieldName] - Panel](https://docs.coveo.com/en/1982/cloud-v2-administrators/add-edit-a-field-fieldname---panel) and [Edit the Mappings of a Source: [SourceName]](https://docs.coveo.com/en/1640/cloud-v2-administrators/edit-the-mappings-of-a-source-sourcename).

## Pushing Documents

The Coveo Push API supports two methods for pushing data: sending a single document, or sending batches of documents.

Unless you are only sending one document, you should always be sending your documents in batches.

### Pushing a Single Document

You should only use this method when you want to add or update a single document. Pushing several documents using this method may lead to the `429 - Too Many Requests` response from the Coveo platform.

Before pushing your document, you should specify the Source Id, Organization Id, and Api Key to use.

```python
push = CoveoPush.Push(sourceId, orgId, apiKey)
```

You can then create a document with the appropriate options, as such:

```python
# Create a document. The paramater passed is its URI. This is mandatory.
mydoc = Document('https://myreference&id=TESTME')
# Set the Title of the document
mydoc.Title = "THIS IS A TEST"
# Set plain text data to your document. This is used for searchability, as well as to generate excerpts and summaries for your document.
mydoc.SetData( "ALL OF THESE WORDS ARE SEARCHABLE")
# Set the file extension of your document. While not mandatory, this option allows Coveo to better analyze your documents.
mydoc.FileExtension = ".html"
# Add metadata to your document. The first option is the field name, while the second is its value.
mydoc.AddMetadata("connectortype", "CSV")
authors = []
authors.append("Coveo")
authors.append("R&D")
# This code assumes that you have a `rssauthors` field set as a multi-value facet in Coveo Cloud.
mydoc.AddMetadata("rssauthors", authors)
```

The above will create a document with the `https://myreference&id=TESTME` URI. It will then set its document text to the value for `SetData`, and add its appropriate metadata.

Once the document is ready, you can push it to your index with the following line:

```python
push.AddSingleDocument(mydoc)
```

A full example would look like this:

```python
from coveopush import CoveoPush
from coveopush import Document
from coveopush import CoveoPermissions
from coveopush import CoveoConstants

sourceId = 'Your Source Id'
orgId = 'Your Org Id'
apiKey = 'Your API Key'

push = CoveoPush.Push(sourceId, orgId, apiKey)
mydoc = Document("https://myreference&id=TESTME")
mydoc.Title = "THIS IS A TEST"
mydoc.SetData("ALL OF THESE WORDS ARE SEARCHABLE")
mydoc.FileExtension = ".html"
mydoc.AddMetadata("connectortype", "CSV")
user_email = "user@coveo.com"
my_permissions = CoveoPermissions.PermissionIdentity(CoveoConstants.Constants.PermissionIdentityType.User, "", user_email)
allowAnonymous = True
mydoc.SetAllowedAndDeniedPermissions([my_permissions], [], allowAnonymous)
push.AddSingleDocument(mydoc)
```

### Pushing Batches of Documents

This SDK offers a convenient way to send batches of documents to the Coveo Cloud platform. Using this method, you ensure that your documents do not get throttled when being sent to Coveo Cloud.

As with the previous call, you must first specify your Source Id, Organization Id, and API Key.

```python
push = CoveoPush.Push(sourceId, orgId, apiKey)
```

You must then start the batch operation, as well as set the maximum size for each batch. If you do not set a maximum size for your request, it will default to 256 Mb. The size is set in bytes.

```python
push.Start(updateSourceStatus, deleteOlder)
push.SetSizeMaxRequest(150*1024*1024)
```

The `updateSourceStatus` option ensures that the source is set to `Rebuild` while documents are being pushed, while the `deleteOlder` option deletes the documents that were already in your source prior to the new documents you are pushing.

You can then start adding documents to your source, using the `Add` command, as such:

```python
push.Add(createDoc('testfiles\\Large1.pptx','1'))
```
For the sake of simplicity, a `createDoc` function is assumed to exist. This function returns documents formatted the same way the `mydoc` element was formatted in the single document example.

The `Add` command checks if the total size of the documents for the current batch does not exceed the maximum size. When it does, it initiates a file upload to Amazon S3, and then pushes this data to Coveo Cloud through the Push API.

Finally, once you are done adding your documents, you should always end the batch operation. This way, the remaining documents will be pushed to the platform, the source status of your Push source will be set back to `Idle`, and old documents will be removed from your source.

The following example demonstrates how to do that.

```python
push = CoveoPush.Push(sourceId, orgId, apiKey)
push.Start(updateSourceStatus, deleteOlder)
push.SetSizeMaxRequest(150*1024*1024)
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
push.End(updateSourceStatus, deleteOlder)
```

## Adding Securities to Your Documents

In Coveo, you can add securities to documents, so only allowed users or groups can view the document. This SDK allows you to add security provider information with your documents while pushing them. To learn how to format your permissions, see [Push API Tutorial 2 - Managing Secured Content](https://docs.coveo.com/en/98/cloud-v2-developers/push-api-tutorial-2---managing-secured-content).

You should first define your security provider, as such:

```python
# First, define a name for your Security Provider
mysecprovidername = "MySecurityProviderTest"

# Then, define the cascading security provider information
cascading = {
              "Email Security Provider": {
                "name": "Email Security Provider",
                "type": "EMAIL"
              }
            }

# Finally, create the provider
push.AddSecurityProvider(mysecprovidername, "EXPANDED", cascading)
```

The `AddSecurityProvider` command automatically associates your current source with the newly created security provider.

Once the security provider is created, you can use it to set permissions on your documents.

The folling example adds a simple permission set:

```python
# Set permissions, based on an email address
user_email = "wim@coveo.com"

# Create a permission identity
my_permission = CoveoPermissions.PermissionIdentity(CoveoConstants.Constants.PermissionIdentityType.User, "", user_email)

# Set the permissions on the document
allowAnonymous = False
my_document.SetAllowedAndDeniedPermissions([my_permission], [], allowAnonymous)
```

The following example incorporates more complex permission sets to your document, in which users can have access to a document either because they are given access individually, or because they belong to a group who has access to the document. This example also includes users who are specifically denied access to the document.

Finally, this example includes two permissions levels. The first permission level has precedence over the second permission level; a user allowed access to a document in the first permission level but denied in the second level will still have access to the document. However, users that are specifically denied access will still not be able to access the document.

```python
# Define a list of users that should have access to the document.
users = []
users.append("wim")
users.append("peter")

# Define a list of users that should not have access to the document.
deniedusers = []
deniedusers.append("alex")
deniedusers.append("anne")

# Define a list of groups that should have access to the document.
groups = []
groups.append("HR")
groups.append("RD")
groups.append("SALES")

# Create the permission Levels. Each level can include multiple sets.
permLevel1 = CoveoPermissions.DocumentPermissionLevel('First')
permLevel1Set1 = CoveoPermissions.DocumentPermissionSet('1Set1')
permLevel1Set2 = CoveoPermissions.DocumentPermissionSet('1Set2')
permLevel1Set1.AllowAnonymous = False
permLevel1Set2.AllowAnonymous = False
permLevel2 = CoveoPermissions.DocumentPermissionLevel('Second')
permLevel2Set = CoveoPermissions.DocumentPermissionSet('2Set1')
permLevel2Set.AllowAnonymous = False

# Set the allowed permissions for the first set of the first level
for user in users:
  # Create the permission identity
  permLevel1Set1.AddAllowedPermission(CoveoPermissions.PermissionIdentity(CoveoConstants.Constants.PermissionIdentityType.User, mysecprovidername, user))

#Set the denied permissions for the second set of the first level
for user in deniedusers:
  # Create the permission identity
  permLevel1Set2.AddDeniedPermission(CoveoPermissions.PermissionIdentity(CoveoConstants.Constants.PermissionIdentityType.User, mysecprovidername, user))

# Set the allowed permissions for the first set of the second level
for group in groups:
 # Create the permission identity
  permLevel2Set.AddAllowedPermission(CoveoPermissions.PermissionIdentity(CoveoConstants.Constants.PermissionIdentityType.Group, mysecprovidername, group))

# Set the permission sets to the appropriate level
permLevel1.AddPermissionSet(permLevel1Set1)
permLevel1.AddPermissionSet(permLevel1Set2)
permLevel2.AddPermissionSet(permLevel2Set)

# Set the permissions on the document
my_document.Permissions.append(permLevel1)
my_document.Permissions.append(permLevel2)
```

Securities are created using permission levels, which can hold multiple PermissionSets (see [Complex Permission Model Definition Example](https://docs.coveo.com/en/25/cloud-v2-developers/complex-permission-model-definition-example)).

Setting securities with a custom security provider also requires that you inform the index of which members and user mappings are available. You would normally do that after the indexing process is complete.

## Adding Security Expansion

A batch call is also available for securities.

To do so, you must first start the security expansion, as such:

```python
push.StartExpansion(my_security_provider_name)
```

Any group you have defined in your security must then be properly expanded, as such:

```python
for group in groups:
  # For each group, define its users
  members = []
  for user in usersingroup:
    # Create a permission identity for each user
    members.append(CoveoPermissions.PermissionIdentityExpansion(CoveoConstants.Constants.PermissionIdentityType.User, mysecprovidername, user))
  push.AddExpansionMember(CoveoPermissions.PermissionIdentityExpansion(CoveoConstants.Constants.PermissionIdentityType.Group, mysecprovidername, group), members, [],[])
```

For each identity, you also need to map it to the email security provider:

```python
for user in users:
  # Create a permission identity
  mappings = []
  mappings.append(CoveoPermissions.PermissionIdentityExpansion(CoveoConstants.Constants.PermissionIdentityType.User, "Email Security Provider", user + "@coveo.com"))
  wellknowns = []
  wellknowns.append(CoveoPermissions.PermissionIdentityExpansion(CoveoConstants.Constants.PermissionIdentityType.Group, mysecprovidername, "Everyone"))
  push.AddExpansionMapping(CoveoPermissions.PermissionIdentityExpansion(CoveoConstants.Constants.PermissionIdentityType.User, mysecprovidername, user), [], mappings, wellknowns)
```

As with the previous batch call, you must remember to end the call, as such:

```python
push.EndExpansion(mysecprovidername)
```

This way, you ensure that the remaining identities are properly sent to the Coveo Platform.

After the next Security Permission update cycle, the securities will be updated (see [Refresh a Security Identity Provider](https://docs.coveo.com/en/1905/cloud-v2-administrators/security-identities---page#refresh-a-security-identity-provider)).

### Dependencies
- [Python 3.x](https://www.python.org/downloads/)
- [Python Requests](http://docs.python-requests.org/en/master/user/install/#install)
- [JSONPickle](https://jsonpickle.github.io/#download-install)

### References
- [Coveo Push API](https://docs.coveo.com/en/68/cloud-v2-developers/push-api)

### Authors
- [Wim Nijmeijer](https://github.com/wnijmeijer)
