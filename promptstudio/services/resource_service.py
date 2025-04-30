import pkg_resources
from aspose.words import License
from google.oauth2.service_account import Credentials
import pickle

class ResourceService:
    
    def __init__(self):
        self.aspose_license_name = '../resources/licenses/Aspose.Total.Product.Family.lic'
        self.gemini_license_path = './resources/licenses/gcp.pickle'
        
    def set_aspose_words_license(self):
        license = License()
        # license_name = 'resources/licenses/Aspose.Total.Product.Family.lic'

        try:
            license_stream = pkg_resources.resource_stream(__name__, self.aspose_license_name)
            license.set_license(license_stream)
        except Exception as e:
            print(f"Error setting Aspose.Words license: {e}")
            raise
        
    def gemini_license(self, scope):
        with open(self.gemini_license_path, 'rb') as file_object:
            gcp_json = pickle.load(file_object)
        credentials = Credentials.from_service_account_info(info = gcp_json,
            scopes=[scope])
        return credentials
        