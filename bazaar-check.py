import requests
import time

class TornAPI:
    def __init__(self):
        self.previous_total_price = None

    def get_torn_user_data(self, user_id, api_key):
        # Use predefined selection "profile,bazaar"
        url = f"https://api.torn.com/user/{user_id}?selections=profile,bazaar&key={api_key}"
        
        try:
            # Make a GET request to the API
            response = requests.get(url)
            
            # Raise an exception for HTTP errors
            response.raise_for_status()
            
            # Parse the response JSON
            data = response.json()
            
            return data
        
        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred: {http_err}")
        except requests.exceptions.RequestException as err:
            print(f"Other error occurred: {err}")
        except Exception as e:
            print(f"An error occurred: {e}")
        return None

    def calculate_bazaar_price_sum(self, data):
        # Calculate the sum of all "price" attributes in the "bazaar" section
        if "bazaar" in data:
            total_price = sum(item["price"] for item in data["bazaar"])
            return total_price
        return 0

    def check_for_purchase(self, user_id, api_key):
        # Get the user data from the API
        data = self.get_torn_user_data(user_id, api_key)
        if data is None:
            return

        # Calculate the current total price in the bazaar
        current_total_price = self.calculate_bazaar_price_sum(data)

        if self.previous_total_price is not None:
            # Compare with the previous total price to detect purchases
            if current_total_price < self.previous_total_price:
                difference = self.previous_total_price - current_total_price
                print(f"Items were purchased! Total spent: {difference}")
            else:
                print("No purchases detected.")
        else:
            print("This is the first check, setting the baseline total price.")

        # Update the previous total price for the next check
        self.previous_total_price = current_total_price

    def start_periodic_check(self, user_id, api_key, interval=30):
        print("Starting periodic checks...")
        while True:
            self.check_for_purchase(user_id, api_key)
            time.sleep(interval)

# Example usage:
api_key = "FUKFxlv59sFjmDNK"
user_id = "3259196"

torn_api = TornAPI()

# Start the periodic checking
torn_api.start_periodic_check(user_id, api_key)
