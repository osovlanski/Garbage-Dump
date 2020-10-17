from __future__ import print_function
from googleapiclient import discovery
from httplib2 import Http
from oauth2client import file, client, tools
from anytree import Node,RenderTree

import os,sys,re

SCOPES = 'https://www.googleapis.com/auth/drive.readonly.metadata'
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

def isPatternInFile(file):
    ans = False
    with open(os.path.join(dirname,'input.txt')) as f:
        words = [word for line in f for word in line.split()].join('|')
        ans = True if re.search(words,file.read().decode('utf-8')) else False
    
    return ans

def get_all_folders_in_drive(fileId):
    files = DRIVE.files().list(q=FILE_QUERY.format(fileId)).execute().get('files', [])
    folders = DRIVE.files().list(q=FOLDER_QUERY.format(fileId)).execute().get('files', [])
    ans = len(files) + len(folders)
    for f in folders:
        ALL_FOLDERS[f['id']] = Node(name={"name":f['name'],"num":0},parent=ALL_FOLDERS[fileId])
        ALL_FOLDERS[f['id']].name['num'] = get_all_folders_in_drive(f['id'])
        ans+=ALL_FOLDERS[f['id']].name['num']
           
    return ans

def read_files():
    command = 0
    currentFolderId = 'root'
    parentsFoldersId = []
    currentFolderName = 'My Drive'
    parentsFoldersName = []
    
    ALL_FOLDERS['root'] = Node(name={"name":'root',"num":0})
    ALL_FOLDERS['root'].name['num'] = get_all_folders_in_drive(currentFolderId)
    
    while True:
        folders = DRIVE.files().list(q=FOLDER_QUERY.format(currentFolderId)).execute().get('files', [])
        print("Results: ")
        for pre, fill, node in RenderTree(ALL_FOLDERS[currentFolderId]):
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