import asyncio
import re
import time
import datetime
import httpx
import imaplib
import email
import sys

class AddressError(Exception):
    pass

def get_premise_id(address):
    url = f"https://selfserve.synergy.net.au/apps/rest/addressSearch/searchPremise.json?query={address}"
    response = httpx.post(url)

    if response.status_code == 200:
        json_data = response.json()
        if json_data:
            if len(json_data) > 0:
                first_item = json_data[0]
                if 'code' in first_item:
                    return first_item['code']
                else:
                    raise Exception("No 'code' value found in the first item.")
            else:
                raise AddressError("No items returned in the JSON response.")
        else:
            raise Exception("No JSON response.")
    else:
        raise Exception(f"Error: {response.status_code}. Failed to fetch data.")


class SynergyDataFetcher:
    def __init__(self, premise_id, email_address, password, email_server, email_port=993, usage_data=None):
        self.premise_id = premise_id
        self.email_address = email_address
        self.password = password
        self.email_server = email_server
        self.email_port = email_port
        self._usage_data = usage_data
        self._client = httpx.Client()

    async def fetch(self, start_date, end_date=datetime.date.today()):
        login_email_response = self._send_email_token()
        if login_email_response.status_code == 200:
            email_token = await self._get_email_token()
            if email_token:
                login_response = self._login_with_email_token(email_token,
                                                              login_email_response.headers.get("Allow-Contract"))
                if login_response.status_code == 200:
                    print("Login successful!")
                    contract_account_number = self._get_contract_account_number()
                    if contract_account_number:
                        device_id = self._get_device_id(contract_account_number)
                        if device_id:
                            self._usage_data = self._get_usage_data(contract_account_number, device_id, start_date,
                                                                    end_date)

                            start_time = datetime.datetime.combine(start_date, datetime.datetime.min.time())
                            self._usage_data["timestamps"] = []
                            for ii in range(0, len(self._usage_data['kwHalfHourlyValues'])):
                                self._usage_data["timestamps"].append(start_time)
                                start_time += datetime.timedelta(minutes=30)

                            return self._usage_data
                else:
                    raise Exception("Failed to login with email token.")
        elif login_email_response.status_code == 400 and "you have had too many attempts" in login_email_response.text:
            print("Too many attempts, try again tomorrow.")
        else:
            raise Exception(f"Web server response did not meet expected conditions. {login_email_response.status_code}")

    def parse(self):
        if not self._usage_data:
            raise ValueError("Usage data has not been fetched yet. Please call retch() first.")

        usage_data = self._usage_data

        peak_kwh = [value if value is not None else 0 for value in usage_data['peakKwhHalfHourlyValues']]
        off_peak_kwh = [value if value is not None else 0 for value in usage_data['offpeakKwhHalfHourlyValues']]
        kw = [value if value is not None else 0 for value in usage_data['kwHalfHourlyValues']]
        kva = [value if value is not None else 0 for value in usage_data['kvaHalfHourlyValues']]
        power_factor = [value if value is not None else 0 for value in usage_data['powerFactorHalfHourlyValues']]
        load_factor = [value if value is not None else 0 for value in usage_data['loadFactorHalfHourlyValues']]
        generation_kwh = [value if value is not None else 0 for value in usage_data['kwhHalfHourlyValuesGeneration']]

        total_kwh = [x + y for x, y in zip(peak_kwh, off_peak_kwh)]

        parsed_usage_data = self._build_data_list(
            ["timestamp", "peak_kwh", "off_peak_kwh", "kw", "kva", "power_factor", "load_factor", "generation_kwh", "total_kwh"],
            usage_data["timestamps"], peak_kwh, off_peak_kwh, kw, kva, power_factor, load_factor, generation_kwh, total_kwh)

        return parsed_usage_data

    def _send_email_token(self):
        print("Sending email token")
        login_url = "https://selfserve.synergy.net.au/apps/rest/emailLogin/getEmailToken"
        login_payload = {'emailAddress': self.email_address, 'premiseId': self.premise_id}
        login_response = self._client.post(login_url, data=login_payload)
        return login_response

    async def _get_email_token(self, timeout=180):
        print("Get email token")
        start_time = time.time()  # Record the start time
        while time.time() - start_time < timeout:
            # Connect to the IMAP server
            mail = imaplib.IMAP4_SSL(self.email_server, self.email_port)
            mail.login(self.email_address, self.password)
            mail.select("inbox")
            # Check if the timeout has occurred
            if time.time() - start_time > timeout:
                print("Timeout occurred. No email token received.")
                break

            # Search for emails with a specific subject
            status, messages = mail.search(None, '(UNSEEN SUBJECT "Your Synergy One-time Passcode")')  #UNSEEN

            if messages[0]:
                # Get the latest email ID
                latest_email_id = messages[0].split()[-1]

                # Fetch the email content
                _, msg_data = mail.fetch(latest_email_id, '(RFC822)')
                raw_email = msg_data[0][1]

                # Decode the email content
                msg = email.message_from_bytes(raw_email)

                email_token = None

                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            body = part.get_payload(decode=True).decode("utf-8")
                            # print(body)

                            # Extract a 6-digit email token using regular expression
                            match = re.search(r'>(\d{6})<', body)
                            if match:
                                email_token = match.group(1)  # print(f"Email Token: {email_token}")
                else:
                    body = msg.get_payload(decode=True).decode("utf-8")
                    # print(body)

                    # Extract a 6-digit email token using regular expression
                    match = re.search(r'>(\d{6})<', body)
                    if match:
                        email_token = match.group()  # print(f"Email Token: {email_token}")

                # Print the extracted email token
                if email_token:
                    print(f"Email Token: {email_token}")
                    mail.logout()
                    return email_token
                else:
                    print("No email token found.")
            else:
                print("No unread emails with email token. Waiting for new emails...")
                await asyncio.sleep(10)  # Adjust the interval as needed

        print("Timeout reached. No email token received within the specified duration.")
        mail.logout()
        return None

    def _login_with_email_token(self, email_token, allow_contract):
        print("Login with email token")
        login_url = "https://selfserve.synergy.net.au/apps/rest/emailLogin/loginWithEmailToken"
        login_payload = {'emailToken': email_token}
        login_response = self._client.post(login_url, json=login_payload,
                                       headers={'Content-Type': 'application/json', 'Allow-Contract': allow_contract})
        return login_response

    def _get_contract_account_number(self):
        print("Getting contract account number")
        index_json_url = "https://selfserve.synergy.net.au/apps/rest/account/index.json"
        index_json_response = self._client.get(index_json_url)
        if index_json_response.status_code == 200:
            json_data = index_json_response.json()
            contract_account_number = json_data[0]['contractAccountNumber']
            if contract_account_number:
                print(f"Contract Account Number: {contract_account_number}")
                return contract_account_number
            else:
                raise Exception("Contract Account Number not found in response JSON.")
        else:
            raise Exception(
                f"Failed to retrieve contract account number. Status code: {index_json_response.status_code}")

    def _get_device_id(self, contract_account_number):
        print("Getting device ID")
        account_json_url = f"https://selfserve.synergy.net.au/apps/rest/account/{contract_account_number}/show.json"
        account_json_response = self._client.get(account_json_url)
        if account_json_response.status_code == 200:
            json_data = account_json_response.json()
            device_id = json_data['installationDetails']['intervalDevices'][0]['deviceId']
            if device_id:
                print(f"Device ID: {device_id}")
                return device_id
            else:
                raise Exception("Device ID not found in response JSON.")
        else:
            raise Exception(f"Failed to retrieve device ID. Status code: {account_json_response.status_code}")

    def _get_usage_data(self, contract_account_number, device_id, start_date, end_date):
        print("Getting usage data")
        usage_json_url = (f'https://selfserve.synergy.net.au/apps/rest/intervalData/'
                          f'{contract_account_number}/getHalfHourlyElecIntervalData?intervalDeviceIds={device_id}&startDate={start_date.strftime("%Y-%m-%d")}&endDate='
                          f'{end_date.strftime("%Y-%m-%d")}')
        usage_json_response = self._client.get(usage_json_url)
        if usage_json_response.status_code == 200:
            json_data = usage_json_response.json()
            if json_data:
                print(f"Usage Data: {json_data}")
                return json_data
            else:
                raise Exception("Device ID not found in response JSON.")
        else:
            raise Exception(f"Failed to retrieve usage data. Status code: {usage_json_response.status_code}")

    def _build_data_list(self, key_names, *value_lists):
        # Check if lengths of input lists are consistent
        lengths = set(len(lst) for lst in value_lists)
        if len(lengths) != 1:
            raise ValueError("Lengths of input lists must be the same")

        if len(value_lists) != len(key_names):
            raise ValueError("Keys and values must have the same length")

        # Initialize an empty dictionary
        result_list = []

        # Iterate over timestamps and value lists simultaneously using zip
        for values in zip(*value_lists):
            value_dict = {}
            for key_name, value in zip(key_names, values):
                value_dict[key_name] = value
            result_list.append(value_dict)

        return result_list


if __name__ == "__main__":
    if len(sys.argv) < 6:
        print("Usage: python script.py <premise_id> <email_address> <password> <email_server> <email_port>")
        sys.exit(1)

    premise_id = sys.argv[1]
    email_address = sys.argv[2]
    password = sys.argv[3]
    email_server = sys.argv[4]

    try:
        email_port = int(sys.argv[5])
    except ValueError:
        print("Error: email_port must be a non-empty integer.")
        sys.exit(1)

    # Perform type and existence checks
    if not premise_id or not isinstance(premise_id, str):
        print("Error: premise_id must be a non-empty string.")
        sys.exit(1)

    if not email_address or not isinstance(email_address, str):
        print("Error: email_address must be a non-empty string.")
        sys.exit(1)

    if not password or not isinstance(password, str):
        print("Error: password must be a non-empty string.")
        sys.exit(1)

    if not email_server or not isinstance(email_server, str):
        print("Error: email_server must be a non-empty string.")
        sys.exit(1)

    if not email_port or not isinstance(email_port, int):
        print("Error: email_port must be a non-empty integer.")
        sys.exit(1)

    synergy_fetcher = SynergyDataFetcher(premise_id, email_address, password, email_server, email_port)
    synergy_fetcher.fetch(datetime.date.today() - datetime.timedelta(days=2))
    parsed_usage_data = synergy_fetcher.parse()
    print(parsed_usage_data)
