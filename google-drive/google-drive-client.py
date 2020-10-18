from __future__ import print_function
from googleapiclient import discovery
from googleapiclient.errors import HttpError
from httplib2 import Http
from oauth2client import file, client, tools
from anytree import Node,RenderTree
from apiclient import http,errors

import slate3k as slate

import os,sys,re,io

# SCOPES = 'https://www.googleapis.com/auth/drive.readonly.metadata'

SCOPES = 'https://www.googleapis.com/auth/drive.readonly'
FILE_QUERY = "mimeType !='application/vnd.google-apps.folder' and '{}' in parents and trashed = false"
FOLDER_QUERY ="mimeType ='application/vnd.google-apps.folder' and '{}' in parents and trashed = false"

dirname = os.path.dirname(__file__)
store = file.Storage(os.path.join(dirname,'storage.json'))
creds = store.get()
if not creds or creds.invalid:
    flow = client.flow_from_clientsecrets(os.path.join(dirname,'client_id.json'), SCOPES)
    creds = tools.run_flow(flow, store)
DRIVE = discovery.build('drive', 'v3', http=creds.authorize(Http()))
ALL_FOLDERS = {}

def getPDFContent(pdfFile):
    s = slate.PDF(io.BytesIO(pdfFile))
    content = ''.join(s)     
    return content + content[::-1] #plaster: check שלום םלוש

#ToDo: improve this with about function
def getCorrectMimeType(file):
    curr = file['mimeType']
    if curr == 'application/vnd.google-apps.document':
        return 'text/plain' 
    if curr == 'application/pdf':
        return 'pdf' 
    if curr == 'application/vnd.google-apps.spreadsheet':
        return 'text/csv'
    return 'No Aviable Type'

def isPatternInFile(file):
    with open(os.path.join(dirname,'input.txt'),encoding='utf-8') as f:
        pattern = '|'.join([word for line in f for word in line.split()]) 

    try:
        mimeType = getCorrectMimeType(file)
        if mimeType == 'No Aviable Type':
            return False
        
        if mimeType == 'pdf': #pdf
            res = DRIVE.files().get_media(fileId=file['id']).execute() # pylint: disable=maybe-no-member
            if res:
                text = getPDFContent(res)
                match = re.search(pattern,text)
            if match:
                return True

        else:  #google docs:
            res = DRIVE.files().export(fileId=file['id'],mimeType=mimeType).execute() # pylint: disable=maybe-no-member
            if res:
                match = re.search(pattern,res.decode('utf-8'))
                if match:
                    return True

    except HttpError:
        print("failed to export file %s %s" % (file['name'],file['mimeType']))
        return False

    return False

def get_all_folders_in_drive_extra(fileId):
    files = DRIVE.files().list(q=FILE_QUERY.format(fileId)).execute().get('files', []) # pylint: disable=maybe-no-member
    folders = DRIVE.files().list(q=FOLDER_QUERY.format(fileId)).execute().get('files', []) # pylint: disable=maybe-no-member
    ans = (len(files) + len(folders),sum(isPatternInFile(f) for f in files))
    for f in folders:
        ALL_FOLDERS[f['id']] = Node(name={"name":f['name'],"num":0,"matched":0},parent=ALL_FOLDERS[fileId])
        curr = get_all_folders_in_drive_extra(f['id'])
        ALL_FOLDERS[f['id']].name['num'] = curr[0]
        ALL_FOLDERS[f['id']].name['matched'] = curr[1]
        ans = (ans[0]+curr[0],ans[1]+curr[1])
           
    return ans


def get_all_folders_in_drive(fileId):
    files = DRIVE.files().list(q=FILE_QUERY.format(fileId)).execute().get('files', []) # pylint: disable=maybe-no-member
    folders = DRIVE.files().list(q=FOLDER_QUERY.format(fileId)).execute().get('files', []) # pylint: disable=maybe-no-member
    ans = len(files) + len(folders)
    for f in folders:
        ALL_FOLDERS[f['id']] = Node(name={"name":f['name'],"num":0},parent=ALL_FOLDERS[fileId])
        ALL_FOLDERS[f['id']].name['num'] = get_all_folders_in_drive(f['id'])
        ans+=ALL_FOLDERS[f['id']].name['num']
           
    return ans

def isExtraOption():
    return any(arg == '-e' for arg in sys.argv[1:])  

def read_files():
    command = 0
    currentFolderId = 'root'
    parentsFoldersId = []
    currentFolderName = 'My Drive'
    parentsFoldersName = []
    
    extraOption = isExtraOption()

    if extraOption:
        ALL_FOLDERS['root'] = Node(name={"name":'root',"num":0,"matched":0})
        ans = get_all_folders_in_drive_extra(currentFolderId)
        ALL_FOLDERS['root'].name['num'] = ans[0]
        ALL_FOLDERS['root'].name['matched'] = ans[1]
    else:
        ALL_FOLDERS['root'] = Node(name={"name":'root',"num":0})
        ALL_FOLDERS['root'].name['num'] = get_all_folders_in_drive(currentFolderId)
    
    while True:
        folders = DRIVE.files().list(q=FOLDER_QUERY.format(currentFolderId)).execute().get('files', []) # pylint: disable=maybe-no-member
        print("Results: ")
        for pre, _, node in RenderTree(ALL_FOLDERS[currentFolderId]):
            if extraOption:
                print("%s%s %d (%d)" % (pre,node.name['name'],node.name['num'],node.name['matched']))
            else:
                print("%s%s %d" % (pre,node.name['name'],node.name['num']))

        print("folders in current files: ")
        for index,f in enumerate(folders):
            print('{})'.format(index+1), f['name'])
        print('{})'.format(len(folders)+1),"..")
        print('{})'.format(len(folders)+2),"Exit")
        command = int(input("Enter which file would you like to check (choose the relevant index from menu)\n"))
        if command == len(folders)+2:#Exit:
            break
        if command == len(folders)+1:#parent
            #swap prev and current
            if len(parentsFoldersId) > 0:
                currentFolderId = parentsFoldersId[-1]
                currentFolderName = parentsFoldersName[-1]
                parentsFoldersId = parentsFoldersId[0:-1]
                parentsFoldersName = parentsFoldersName[0:-1]
        else:
            parentsFoldersId.append(currentFolderId)
            parentsFoldersName.append(currentFolderName)
            currentFolderId = folders[command-1]['id']
            currentFolderName = folders[command-1]['name']

def main():
    read_files()

if __name__ == "__main__":
    main()