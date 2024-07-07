import os
from azure.storage.blob import BlobServiceClient


def upload_file_to_blob_storage(
    connection_string, container_name, directory_name, file_path
):
    """
    Upload a file to a specific directory within a container in Azure Blob Storage.

    """

    blob_service_client = BlobServiceClient.from_connection_string(connection_string)

    try:
        container_client = blob_service_client.create_container(container_name)
        print(f"Container '{container_name}' created successfully.")
    except Exception as e:
        print(f"Container might already exist: {e}")

    blob_name = f"{directory_name}/{os.path.basename(file_path)}"
    blob_client = blob_service_client.get_blob_client(
        container=container_name, blob=blob_name
    )

    with open(file_path, "rb") as data:
        blob_client.upload_blob(data)
    print(
        f"File '{file_path}' uploaded to '{blob_name}' in container '{container_name}'."
    )


def download_file_from_blob_storage(
    connection_string, container_name, blob_name, download_path
):
    """
    Download a file from a specific blob within a container in Azure Blob Storage.

    """
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)

    blob_client = blob_service_client.get_blob_client(
        container=container_name, blob=blob_name
    )

    with open(download_path, "wb") as download_file:
        download_file.write(blob_client.download_blob().readall())
    print(
        f"File '{blob_name}' downloaded to '{download_path}' from container '{container_name}'."
    )
