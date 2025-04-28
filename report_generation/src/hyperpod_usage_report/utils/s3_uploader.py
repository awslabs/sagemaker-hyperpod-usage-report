import os

import boto3


class S3Uploader:
    @staticmethod
    def upload_file(file_path: str, output_location: str) -> None:
        try:
            s3_client = boto3.client("s3")
            parts = output_location.rstrip('/').split("/")
            bucket = parts[2]
            key = f"{'/'.join(parts[3:])}/{os.path.basename(file_path)}"

            s3_client.upload_file(file_path, bucket, key)
            print(
                f"Report uploaded successfully to {output_location}{os.path.basename(file_path)}"
            )
        except Exception as e:
            print(f"Error uploading to S3: {str(e)}")
            raise
