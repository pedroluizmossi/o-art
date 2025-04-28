import httpx
from dotenv import load_dotenv

from model.user_model import User

from core.env_core import Envs, get_env_variable

from core.logging_core import setup_logger

# Set up the logger for this module
logger = setup_logger(__name__)

load_dotenv()

FIEF_API_URL = get_env_variable(Envs.FIEF_API_URL)
FIEF_USERS_API_URL = f"{FIEF_API_URL}/users/"
FIEF_API_USER_TOKEN = get_env_variable(Envs.FIEF_API_USER_TOKEN)

class FiefHttpClient:
    """
    A client for interacting with the Fief API.
    """

    def __init__(self):
        self.base_url = FIEF_USERS_API_URL
        self.headers = {
            "Authorization": f"Bearer {FIEF_API_USER_TOKEN}",
            "Content-Type": "application/json",
        }
        self.client = httpx.Client(base_url=self.base_url, headers=self.headers)

    def get_all_users(self) -> list:
        """
        Retrieve all users from Fief.

        Returns:
            list: A list of users.
        """
        try:
            response = self.client.get(self.base_url)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"An error occurred: {str(e)}")
            raise

    def get_user(self, user_id: str) -> dict:
        """
        Retrieve a user by ID from Fief.

        Args:
            user_id (str): The ID of the user to retrieve.

        Returns:
            dict: The user data.
        """
        try:
            response = self.client.get(f"{self.base_url}{user_id}/")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"An error occurred: {str(e)}")
            raise

