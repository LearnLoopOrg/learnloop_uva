    def save_image_locally(self, image_content, image_path):
        """
        Save the image content to the specified local path.
        """
        # Ensure the directory structure exists
        os.makedirs(os.path.dirname(image_path), exist_ok=True)

        # Write the image content to the local file
        with open(image_path, "wb") as image_file:
            image_file.write(image_content)

    def render_image(self):
        """
        Render the image in the Streamlit app using its base64 representation.
        """
        # Get the image name from the blob url
        if "url" in st.session_state.segment_content["image"]:
            image_blob_name = st.session_state.segment_content["image"]["url"].split(
                "/"
            )[-1]

        image_blob_name = "celbio_3/slide_00000_2.jpg"

        # Get the connection string and local image path
        connection_string = os.getenv("AZURE_BLOB_STORAGE_CONNECTION_STRING")
        local_image_path = f"src/data/content/images/{image_blob_name.split('/')[-1]}"

        image_content = self.get_image_from_blob(
            image_blob_name, st.session_state.container_name, connection_string
        )

        self.save_image_locally(image_content, local_image_path)

        # Convert the image to base64
        image_base64 = self.convert_image_to_base64(local_image_path)
        st.image(f"data:image/png;base64,{image_base64}", width=100)

    def get_image_from_blob(self, blob_name, container_name, connection_string):
        """
        Download an image from a specific blob within a container in Azure Blob Storage.
        """
        blob_service_client = BlobServiceClient.from_connection_string(
            connection_string
        )

        blob_client = blob_service_client.get_blob_client(
            container=container_name, blob=blob_name
        )

        # Download the blob's content as bytes
        blob_content = blob_client.download_blob().readall()

        return blob_content

    def convert_image_to_base64(self, image_path):
        """
        Convert the image at the specified path to a base64 string.
        """
        with open(image_path, "rb") as image_file:
            image_bytes = image_file.read()
            image_base64 = base64.b64encode(image_bytes).decode("utf-8")

        return image_base64