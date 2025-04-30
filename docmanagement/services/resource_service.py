import pkg_resources
from aspose.words import License

class ResourceService:
    
    def __init__(self):
        self.aspose_license_name = '../resources/licenses/Aspose.Total.Product.Family.lic'
        
    def set_aspose_words_license(self):
        license = License()
        # license_name = 'resources/licenses/Aspose.Total.Product.Family.lic'

        try:
            license_stream = pkg_resources.resource_stream(__name__, self.aspose_license_name)
            license.set_license(license_stream)
        except Exception as e:
            print(f"Error setting Aspose.Words license: {e}")
            raise