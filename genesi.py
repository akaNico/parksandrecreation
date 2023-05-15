from ast import Constant
# do "pip install requests"
import requests
import random
import os
import base64
import json
import datetime
import pytz
import sys
# do "pip install PyGithub"
from github import Github
import argparse

parser = argparse.ArgumentParser(description='Parse parameters')
parser.add_argument('--accounts_ondemand', type=str,
                    help='A comma-separated list of integers', default='')
parser.add_argument('--faster', action='store_true',
                    help='A boolean flag', default=False)
args = parser.parse_args()

accounts_ondemand_value = None
if args.accounts_ondemand:
    accounts_ondemand_value = args.accounts_ondemand

old_script = None
if args.old:
    old_script = args.faster

ids_array = []
# Usa il valore del parametro "accounts_ondemand_value"
if accounts_ondemand_value is not None:
    print(
        f"Il valore del parametro 'accounts_ondemand' è: {accounts_ondemand_value}")
    ids_array = accounts_ondemand_value.split(",")

# Set the path of the folder to upload to the repository
FOLDER_PATH = "habanero"
filename_original = ".github/workflows/workflow_proxed.yml"
if old_script:
    filename_original = ".github/workflows/workflow_orig.yml"
filename_original_az = ".github/workflows/workflow_orig_az_createrun.yml"

ACCOUNTS = os.environ['GH_ACCOUNTS_B64']
ACCOUNTS = base64.b64decode(ACCOUNTS).decode("utf-8")
# print(ACCOUNTS)

data = json.loads(ACCOUNTS)

message = "Jobs will start at:\n"
# set in CET
startHours = 7
endHours = 9
array_messages = []

if len(ids_array) > 0:
    # ottieni la data e l'ora corrente
    now = datetime.datetime.now(pytz.timezone('CET'))
    # aggiungi un'ora
    future_time = now + datetime.timedelta(hours=1, minutes=0)
    # assegna ore e minuti a due variabili separate
    ora = future_time.hour
    # set in CET
    startHours = ora
    endHours = ora


for item in data:
    print("ID: ", item["id"])
    print("Account: ", item["account"])
    # print("Token: "    , item["token"])

    username = item["account"]
    id = item["id"]

    url = f"https://www.github.com/{username}"
    response = requests.get(url)

    if response.status_code == 404:
        array_messages.append(f"DISABLED {id} {username}\n")
        continue

    if len(ids_array) > 0 and item["id"] not in ids_array:
        print(f'{item["id"]} skipped')
        continue

    print(f'Creating for id {item["id"]}')

    try:
        # Instantiate the Github object using the access token
        g = Github(item["token"])

        # Delete all GH account repositories
        user = g.get_user()
        repos = user.get_repos()
        for repo in repos:
            repo.delete()

        response = requests.get(
            "https://api.datamuse.com/words", params={"rel_jjb": "cool"})
        first_word = random.choice(response.json())["word"]
        response = requests.get(
            "https://api.datamuse.com/words", params={"rel_jjb": "project"})
        second_word = random.choice(response.json())["word"]
        REPO_NAME = f"{first_word}-{second_word}"
        print(REPO_NAME)

        hour = random.randint(startHours, endHours)
        minute = random.randint(0, 59)
        # set in UTC
        cron = f"{minute} {hour-2} * * *"

        # message = message + f"{hour}:{minute} for {item['id']} - {item['account']}\n"
        # message = message + f"{str(hour).zfill(2)}:{str(minute).zfill(2)} for {str(item['id']).zfill(3)} - {item['account']}\n"
        array_messages.append(
            f"{str(hour).zfill(2)}:{str(minute).zfill(2)} for {str(item['id']).zfill(3)} - {item['account']}\n")
        repo = g.get_user().create_repo(REPO_NAME)
        print(f"Repository {REPO_NAME} creata correttamente")

        print('Add files to repository')
        filename_output = f".github/workflows/{REPO_NAME}.yml"
        with open(os.path.join(FOLDER_PATH, filename_original), 'r') as file:
            filedata = file.read()
        filedata = filedata.replace('__name__', REPO_NAME)
        filedata = filedata.replace('__cron__', cron)
        filedata = filedata.replace('__affinity__', item["id"])
        filedata = filedata.replace('__account__', item["account"])
        with open(os.path.join(FOLDER_PATH, filename_output), 'w') as file:
            file.write(filedata)

        print('Add files to repository az')
        # set in UTC
        cron = f"{minute} {hour-2} * * *"
        filename_output_az = f".github/workflows/{REPO_NAME}_az.yml"
        with open(os.path.join(FOLDER_PATH, filename_original_az), 'r') as file:
            filedata = file.read()
        filedata = filedata.replace('__name__', REPO_NAME)
        filedata = filedata.replace('__cron__', cron)
        filedata = filedata.replace('__affinity__', item["id"])
        filedata = filedata.replace('__account__', item["account"])
        with open(os.path.join(FOLDER_PATH, filename_output_az), 'w') as file:
            file.write(filedata)

        # Add the files from the folder to the repository
        exclude_list = ["workflow_orig.yml",
                        ".DS_Store",
                        "workflow_orig_az.yml",
                        "workflow_faster.yml",
                        "workflow_proxed.yml",
                        "workflow_orig_az_createrun.yml"]
        for dirname, _, filenames in os.walk(FOLDER_PATH):
            for filename in filenames:
                if filename in exclude_list:
                    continue
                file_path = os.path.join(dirname, filename)
                with open(file_path, "rb") as f:
                    contents = f.read()
                file_path_relative = os.path.relpath(file_path, FOLDER_PATH)
                print(file_path_relative)
                repo.create_file(file_path_relative,
                                 f"Added {file_path_relative}", contents)
        os.remove(f"{FOLDER_PATH}/{filename_output}")
        os.remove(f"{FOLDER_PATH}/{filename_output_az}")
        print('Add files to repository completed')

        print('Creation secret')
        # Create the secret using the create_secret() method
        repo.create_secret("GOOGLE_SHEETS_TAB_NAME",
                           os.environ['GOOGLE_SHEETS_TAB_NAME'])
        repo.create_secret("GOOGLE_SHEETS_TOKEN_B64",
                           os.environ['GOOGLE_SHEETS_TOKEN_B64'])
        repo.create_secret("GOOGLE_SHEETS_SHEET_ID",
                           os.environ['GOOGLE_SHEETS_SHEET_ID'])
        repo.create_secret("GOOGLE_SHEETS_CREDENTIALS_B64",
                           os.environ['GOOGLE_SHEETS_CREDENTIALS_B64'])
        repo.create_secret("TELEGRAM_API_TOKEN",
                           os.environ['TELEGRAM_API_TOKEN'])
        repo.create_secret("TELEGRAM_USERID", os.environ['TELEGRAM_USERID'])
        repo.create_secret("GPG_PASSPHRASE", os.environ['GPG_PASSPHRASE'])
        repo.create_secret("CONTAINER_IMAGE", os.environ['CONTAINER_IMAGE'])
        repo.create_secret("CONTAINER_USER", os.environ['CONTAINER_USER'])
        repo.create_secret("CONTAINER_PASS", os.environ['CONTAINER_PASS'])
        repo.create_secret("MATRIX", os.environ['MATRIX'])
        repo.create_secret("PROXY_LIST_URL", os.environ['PROXY_LIST_URL'])
        repo.create_secret("AZURE_CREDENTIALS",
                           os.environ['AZURE_CREDENTIALS'])
        print(f"Secret set correctly in the repository {REPO_NAME}.")

        # Abilita le Actions nel repository
        # Sostituisci con i tuoi dati
        personal_access_token = item["token"]
        owner = item["account"]

        # Costruisci l'URL dell'API REST di GitHub
        url = f"https://api.github.com/repos/{owner}/{REPO_NAME}/actions/permissions"

        # Costruisci il payload della richiesta
        payload = {
            "enabled": True,
            "allowed_actions": "all"
        }

        # Aggiungi gli header richiesti
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"token {personal_access_token}",
            "X-GitHub-Api-Version": "2022-11-28"
        }

        # Esegui la richiesta HTTP PUT per abilitare le Actions nel repository
        response = requests.put(url, json=payload, headers=headers)

        # Verifica la risposta
        if response.status_code == 204:
            print("Le Actions sono state abilitate con successo nel repository.")
        else:
            print(
                f"Si è verificato un errore durante l'abilitazione delle Actions. Codice di stato: {response.status_code}")

        print("----------------------------------------------------")

    except Exception as e:
        # If an error occurs, add the error message to the message string
        # message = message + f"{str(item['id']).zfill(3)} - {item['account']} - Error: {str(e)}\n"
        array_messages.append(
            f"ERRORE: {str(item['id']).zfill(3)} - {item['account']} - Error: {str(e)}\n")
        continue

array_messages.sort()
messages_concat = ''.join(array_messages)
message = message + messages_concat

# Send notification to telegram
print("Send notification to telegram")
TOKEN = os.environ['TELEGRAM_API_TOKEN']
chat_id = os.environ['TELEGRAM_USERID']
url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={chat_id}&text={message}"
print(requests.get(url).json())  # this sends the message
