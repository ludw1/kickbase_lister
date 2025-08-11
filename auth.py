import requests
from dotenv import load_dotenv
import os
load_dotenv()
class User:
   def __init__(self, req_response: dict):
    user_dict = req_response.get("u", {})
    self.id = user_dict.get("id")
    self.name = user_dict.get("name")
    self.email = user_dict.get("email")
    self.leagues = user_dict.get("srvl", [])
    self.token : str = req_response.get("tkn", "")
      
def login() -> User:
  """Login the user with enviroment set email and password.

  Returns:
      dict: User object containing user details.
  Raises:
      Exception: If the login fails.
  """  
  url = "https://api.kickbase.com/v4/user/login"
  # JSON payload for the request
  # user needs to add email and password

  payload = {
    "em": os.getenv("EMAIL"),
    "loy": False,
    "pass": os.getenv("PASSWORD"),
    "rep": {}
  }

  # headers for the request
  headers = {
      "Content-Type": "application/json",
      "Accept": "application/json"
  }

  # sending the POST request
  response = requests.post(url, json=payload, headers=headers)
  # Extracting the token from the response JSON
  if response.status_code == 200:
      user = User(response.json())
  else:
      raise Exception(f"Login failed: {response.status_code} - {response.text}")
  return user
