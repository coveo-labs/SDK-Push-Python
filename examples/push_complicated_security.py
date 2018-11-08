#!/usr/bin/env python
#-------------------------------------------------------------------------------------
# Push single document with complicated security
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

from coveopush import CoveoPush
from coveopush import Document
from coveopush import CoveoPermissions
from coveopush import CoveoConstants

def main():
    sourceId = '--Enter your source id--'
    orgId = '--Enter your org id--'
    apiKey = '--Enter your API key--'

    # Setup the push client
    push = CoveoPush.Push(sourceId, orgId, apiKey)

    # First set the securityprovidername
    mysecprovidername = "MySecurityProviderTest"
    # Define cascading security provider information
    cascading = {
                  "Email Security Provider": {
                    "name": "Email Security Provider",
                    "type": "EMAIL"
                  }
                }

    # Create it
    push.AddSecurityProvider(mysecprovidername, "EXPANDED", cascading)
    startOrderingId = push.CreateOrderingId()
    # Delete all old entries
    push.DeletePermissionsOlderThan(mysecprovidername, startOrderingId)
    print ("Old ids removed. Updating security cache")
    input ("Press any key to continue...")

    # Create a document
    mydoc = Document('https://myreference&id=TESTMESECURITY')
    # Set the content. This will also be available as quickview for that document.
    content = "<meta charset='UTF-16'><meta http-equiv='Content-Type' content='text/html; charset=UTF-16'><html><head><title>My First Title</title><style>.datagrid table { border-collapse: collapse; text-align: left; } .datagrid {display:table !important;font: normal 12px/150% Arial, Helvetica, sans-serif; background: #fff; overflow: hidden; border: 1px solid #006699; -webkit-border-radius: 3px; -moz-border-radius: 3px; border-radius: 3px; }.datagrid table td, .datagrid table th { padding: 3px 10px; }.datagrid table thead th {background:-webkit-gradient( linear, left top, left bottom, color-stop(0.05, #006699), color-stop(1, #00557F) );background:-moz-linear-gradient( center top, #006699 5%, #00557F 100% );filter:progid:DXImageTransform.Microsoft.gradient(startColorstr='#006699', endColorstr='#00557F');background-color:#006699; color:#FFFFFF; font-size: 15px; font-weight: bold; border-left: 1px solid #0070A8; } .datagrid table thead th:first-child { border: none; }.datagrid table tbody td { color: #00496B; border-left: 1px solid #E1EEF4;font-size: 12px;font-weight: normal; }.datagrid table tbody  tr:nth-child(even)  td { background: #E1EEF4; color: #00496B; }.datagrid table tbody td:first-child { border-left: none; }.datagrid table tbody tr:last-child td { border-bottom: none; }</style></head><body style='Font-family:Arial'><div class='datagrid'><table><tbody><tr><td>FirstName</td><td>Willem</td></tr><tr><td>MiddleName</td><td>Van</td></tr><tr><td>LastName</td><td>Post</td></tr><tr><td>PositionDescription</td><td>VP Engineering</td></tr><tr><td>JobFunction</td><td>CTO</td></tr><tr><td>JobFamily</td><td>Management</td></tr></tbody></table></div></body></html>"
    mydoc.SetContentAndZLibCompress(content)
    # Set the metadata
    mydoc.AddMetadata("connectortype","CSV")
    authors = []
    authors.append( "Coveo" )
    authors.append( "R&D" )
    # rssauthors should be set as a multi-value field in your Coveo Cloud organization
    mydoc.AddMetadata("rssauthors", authors)
    # Set the title
    mydoc.Title = "THIS IS A TEST"

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
    mydoc.Permissions.append(permLevel1)
    mydoc.Permissions.append(permLevel2)

    # Push the document
    push.AddSingleDocument(mydoc)

    # First do a single call to update an identity
    # We now also need to add the expansion/memberships/mappings to the security cache
    # The previouslt defined identities were: alex, anne, wim, peter
    
    usersingroup = []
    usersingroup.append("wimingroup")
    usersingroup.append("peteringroup")

    # Remove the last group, so we can add it later with a single call
    groups.pop()

    push.StartExpansion( mysecprovidername )
    # group memberships for: HR, RD
    for group in groups:
      # for each group set the users
      members = []
      for user in usersingroup:
        # Create a permission Identity
        members.append(CoveoPermissions.PermissionIdentityExpansion( CoveoConstants.Constants.PermissionIdentityType.User, mysecprovidername, user ))
      push.AddExpansionMember(CoveoPermissions.PermissionIdentityExpansion( CoveoConstants.Constants.PermissionIdentityType.Group, mysecprovidername, group ), members, [],[] )

    # mappings for all users, from userid to email address
    users.extend(deniedusers)
    users.extend(usersingroup)
    for user in users:
      # Create a permission Identity
      mappings=[]
      mappings.append(CoveoPermissions.PermissionIdentityExpansion( CoveoConstants.Constants.PermissionIdentityType.User, "Email Security Provider", user+"@coveo.com" ))
      wellknowns=[]
      wellknowns.append(CoveoPermissions.PermissionIdentityExpansion( CoveoConstants.Constants.PermissionIdentityType.Group, mysecprovidername, "Everyone"))
      push.AddExpansionMapping(CoveoPermissions.PermissionIdentityExpansion( CoveoConstants.Constants.PermissionIdentityType.User, mysecprovidername, user ), [], mappings, wellknowns )

    # Remove deleted users
    # Deleted Users
    delusers = []
    delusers.append("wimn")
    delusers.append("petern")
    for user in delusers:
      # Add each identity to delete to the Deleted
      push.AddExpansionDeleted(CoveoPermissions.PermissionIdentityExpansion( CoveoConstants.Constants.PermissionIdentityType.User, mysecprovidername, user ),[],[],[])

    # End the expansion and write the last batch
    push.EndExpansion( mysecprovidername )

    print ("Now updating security cache.")
    print ("Check:")
    print (" HR/RD groups: members wimingroup, peteringroup")
    print (" SALES: should not have any members")
    print (" each user: wim, peter, anne, wimingroup should have also mappings to Email security providers")
    input ("Press any key to continue...")

    # Add a single call, add the Sales group
    usersingroup = []
    usersingroup.append("wiminsalesgroup")
    usersingroup.append("peterinsalesgroup")

    members = []
    for user in usersingroup:
      # Create a permission identity
      mappings = []
      mappings.append(CoveoPermissions.PermissionIdentityExpansion(CoveoConstants.Constants.PermissionIdentityType.User, "Email Security Provider", user + "@coveo.com"))
      wellknowns = []
      wellknowns.append(CoveoPermissions.PermissionIdentityExpansion(CoveoConstants.Constants.PermissionIdentityType.Group, mysecprovidername, "Everyone"))
      members.append(CoveoPermissions.PermissionIdentityExpansion(CoveoConstants.Constants.PermissionIdentityType.User, mysecprovidername, user))
      push.AddPermissionExpansion(mysecprovidername, CoveoPermissions.PermissionIdentityExpansion(CoveoConstants.Constants.PermissionIdentityType.User, mysecprovidername, user), [], mappings, wellknowns)

    push.AddPermissionExpansion(mysecprovidername, CoveoPermissions.PermissionIdentityExpansion( CoveoConstants.Constants.PermissionIdentityType.Group, mysecprovidername, "Everyone"), members, [],[])
    push.AddPermissionExpansion(mysecprovidername, CoveoPermissions.PermissionIdentityExpansion( CoveoConstants.Constants.PermissionIdentityType.Group, mysecprovidername, "SALES"), members, [],[])

    print ("Now updating security cache.")
    print ("Check:")
    print (" HR/RD groups: members wimingroup, peteringroup")
    print (" SALES: should have members wiminsalesgroup, peterinsalesgroup")
    print (" each user: wim, peter, anne, wimingroup should also have mappings to Email security providers")
    input ("Press any key to continue...")

    # Remove a Identity
    # Group SALES should be removed
    push.RemovePermissionIdentity(mysecprovidername, CoveoPermissions.PermissionIdentityExpansion( CoveoConstants.Constants.PermissionIdentityType.Group, mysecprovidername, "SALES"))
    print ("Now updating security cache.")
    print ("Check:")
    print (" HR/RD groups: members wimingroup,peteringroup")
    print (" NO wiminsalesgroup,peterinsalesgroup")
    print (" each user: wim, peter, anne, wimingroup should have also mappings to Email security providers")

if __name__ == '__main__':
    main()
