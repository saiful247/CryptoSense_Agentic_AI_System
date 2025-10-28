import os
import json
import vertexai
from dotenv import load_dotenv
from vertexai.preview.vision_models import ImageGenerationModel
from google.oauth2 import service_account

from google.cloud import storage
import pandas as pd
from io import BytesIO

# Load .env variables
load_dotenv()

project_id = os.getenv("PROJECT_ID")
location = os.getenv("LOCATION")


# if os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
#     credentials = service_account.Credentials.from_service_account_file(
#         os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
#     )
credentials = None

# Initialize Vertex AI
vertexai.init(project=project_id, location=location, credentials=credentials)

# Use Imagen 2
model = ImageGenerationModel.from_pretrained("imagen-4.0-generate-001")


def generateNftImage():
    def nft_image_generation_function(state):
        nftPrompt = state.get("nftPrompt", "")
        nftName = state.get("input", {}).get("nftName", "unnamed_nft")
        nftCollectionName = state.get("input", {}).get(
            "nftCollectionName", "default_collection")

        print("Generating image with prompt: ", nftPrompt)

        result = model.generate_images(
            prompt=nftPrompt,
            number_of_images=1,
        )

        # Save image
        # for idx, image in enumerate(result.images):
        #     image.save(f"nft_art_{idx}.png")

        bucket_name = ""
        blob_name = f"nft_images/{nftCollectionName}_{nftName}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.png"

        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)

        image = result.images[0]
        image_bytes = image._image_bytes

        buffer = BytesIO(image_bytes)
        # image.save(buffer, format="PNG")
        # buffer.seek(0)

        blob.upload_from_file(buffer, content_type="image/png")

        gcp_bucket_url = f"https://storage.googleapis.com/{bucket_name}/{blob_name}"

        state["nftURL"] = gcp_bucket_url
        return state
    return nft_image_generation_function
