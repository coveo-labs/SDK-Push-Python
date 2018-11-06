# Coveo Push API SDK for Python

The Coveo Push API SDK for Python is meant to help you use the [Coveo Push API](https://docs.coveo.com/en/68/cloud-v2-developers/push-api) using Python.

The SDK makes it easier to communicate with the Coveo Push API when using Python.

- Document validation before they are pushed to the plaform
- Update source status before and after a document update
- Large files are automatically pushed to the platform through an Amazon S3 container

For code examples on how to use the SDK, see the `examples` section.

## Installation
Make sure you have installed [git](https://git-scm.com/downloads).

Then, enter the following command in your command prompt.

```
pip install git+https://github.com/coveo-labs/SDK-Push-Python
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

## Pushing Documents

The Coveo Push API supports two methods for pushing data: single calls and batch calls. Almost all of the time, you are encouraged to use batch calls over single calls. Using single calls is usually recommended only when adding or updating a single document.

This SDK offers two methods of pushing documents: pushing a single document, or pushing a batch of document.

For most use cases, the third approach is the recommended approach.

### Pushing a Single Document

You should only use this method when you want to add or update a single document. Pushing several documents using this method may lead to the `429 - Too Many Requests` response from the Coveo Platform.

Before pushing your document, you should specify the Source Id, Organization Id, and Api Key to use.

```python
push = CoveoPush.Push(sourceId, orgId, apiKey)
```

You can then create a document with the appropriate options, as such:

```python
# Create a document. The paramater passed is its URI.
mydoc = Document('https://myreference&id=TESTME')
# Set the Title of the document
mydoc.Title = "THIS IS A TEST"
# Set plain text data to your document.
mydoc.SetData( "ALL OF THESE WORDS ARE SEARCHABLE")
# Set the file extension of your document
mydoc.FileExtension = ".html"
# Add metadata to your document. The first option is the field name, while the second is its value.
mydoc.AddMetadata("connectortype", "CSV")
authors = []
authors.append("Coveo")
authors.append("R&D")
# rssauthors is a MultiFacet field
mydoc.AddMetadata("rssauthors", authors)
```

The above will create a document with a documentid of `https://myreference&id=TESTME`. It will set its document text to the value for `SetData`, and add its appropriate metadata.
some metadata and other properties like `FileExtension` and `Title`.

Once the document is ready, you can push it to your index with the following line:

```python
push.AddSingleDocument(mydoc)
```

Example:

```python
push = CoveoPush.Push(sourceId, orgId, apiKey)
mydoc = CoveoDocument("https://myreference&id=TESTME")
mydoc.Title = "THIS IS A TEST"
mydoc.SetData("ALL OF THESE WORDS ARE SEARCHABLE")
mydoc.FileExtension = ".html"
mydoc.AddMetadata("connectortype", "CSV")
user_email = "wim@coveo.com"
my_permissions = CoveoPermissions.PermissionIdentity(CoveoConstants.Constants.PermissionIdentityType.User, "", user_email)
allowAnonymous = True
mydoc.SetAllowedAndDeniedPermissions([my_permissions], [], allowAnonymous)
push.AddSingleDocument(mydoc)
```

### Pushing Batches of Documents

You should use this method when you want to push several documents at the same time to the platform.

As with the previous call, you must first specify your Source Id, Organization Id, and API Key.

```python
push = CoveoPush.Push(sourceId, orgId, apiKey)
```

You must then start the batch operation, as well as set the maximum size for each batch. If you do not set a maximum size for your request, it will default to 256 Mb.

```python
push.Start(updateSourceStatus, deleteOlder)
push.SetSizeMaxRequest(150*1024*1024)
```

The `updateSourceStatus` option ensures that the source is set to `Rebuild` while documents are being pushed, while the `deleteOlder` option deletes the documents that were already in your source prior to the new documents you are pushing.

You can then start adding documents to your source, using the `Add` command, as such:

```python
push.Add(createDoc('testfiles\\Large1.pptx','1'))
```

This command checks if the total size of the documents for the current batch does not exceed the maximum size. When it does, it will initiate a file upload to Amazon S3, and then push this data to Coveo Cloud through the Push API.

Finally, once you are done adding your documents, you should always end the stream. This way, the remaining documents will be pushed to the platform, the source status of your Push source will be set back to `Idle`, and old documents will be removed from your source.

Example:

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

## Adding Securities and Permissions to Your Documents

In many circumstances, you may also want to add securities and permissions to the documents you are pushing. This SDK allows ou to add security provider information with your documents while pushing them. To learn how to format your permissions, see [Push API Tutorial 2 - Managing Secured Content](https://docs.coveo.com/en/98/cloud-v2-developers/push-api-tutorial-2---managing-secured-content).

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

The `AddSecurityProvider` will automatically associate your current source with the newly created security provider.

Once the security provider is created, you can use it to set permissions on your documents.

This example is for a simple permission set:

```python
# Set permissions, based on an email address
user_email = "wim@coveo.com"

# Create a permission identity
my_permission = CoveoPermissions.PermissionIdentity(CoveoConstants.Constants.PermissionIdentityType.User, "", user_email)

# Set the permissions on the document
allowAnonymous = False
my_document.SetAllowedAndDeniedPermissions([my_permission], [], allowAnonymous)
```

This example incorporates more complex permission sets to your document, in which users can have access to a document either because they are given access individually, or they belong to a group who has access to the document. This example also includes user who are specifically denied access to the document.

Finally, this example includes two permissions levels, the first one based on the individuals, while the second is based on groups. The first permission level has precedence over the second permission level; a user allowed access to a document in the first permission level but denied in the second level will still have access to the document. However, users that are specifically denied access will still not be able to access the document.

```python
# Set permissions
# Specific Users have permissions (in permLevel1/permLevel1Set) OR if you are in the group (permLevel2/permLevel2Set)
# This means: Two PermissionLevels
# Higher Permission Levels means priority
# So if you are allowed in Permission Level 1 and denied in Permission Level 2 you will still have access
# Denied users will always filtered out

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

# Set the permission sets to the levels
permLevel1.AddPermissionSet(permLevel1Set1)
permLevel1.AddPermissionSet(permLevel1Set2)
permLevel2.AddPermissionSet(permLevel2Set)

# Set the permissions on the document
my_document.Permissions.append(permLevel1)
my_document.Permissions.append(permLevel2)
```

Permissions are created using permission levels, which can hold multiple PermissionSets (see [Complex Permission Model Definition Example](https://docs.coveo.com/en/25/cloud-v2-developers/complex-permission-model-definition-example)).

Setting permissions with a custom security provider also requires that you inform the index which members and user mappings are available. You would normally do that after the indexing process is complete.

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

After the next Security Permission Update cycle, the securities will be updated (see [Refresh a Security Identity Provider](https://docs.coveo.com/en/1905/cloud-v2-administrators/security-identities---page#refresh-a-security-identity-provider)).

### Dependencies
* [Python 3.x](https://www.python.org/downloads/)
* [Python Requests library]

### References
* [Coveo Push API](https://docs.coveo.com/en/68/cloud-v2-developers/push-api)

### Authors
- [Wim Nijmeijer](https://github.com/wnijmeijer)
