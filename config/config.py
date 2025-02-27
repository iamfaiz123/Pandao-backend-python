import os
from dotenv import load_dotenv

def load_env(filepath='./.env'):
    """Loads environment variables from a .env file.

    Args:
        filepath: The path to the .env file.

    Returns:
        A dictionary-like object containing the environment variables, or None if an error occurs.
    """
    try:
        load_dotenv(dotenv_path=filepath)  # Load the .env file
        env_vars = dict(os.environ) # return all environment variables as a dictionary
        return env_vars
    except FileNotFoundError:
        print(f"Error: .env file not found at {filepath}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None
config = load_env()


