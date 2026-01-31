import os
import io
from minio import Minio
from minio.error import S3Error

def get_minio_client() -> Minio:
    """Initialize MinIO client using environment variables."""

    endpoint = os.getenv("MINIO_ENDPOINT", "minio:9000")
    access_key = os.getenv("MINIO_ROOT_USER", "terra_admin")
    secret_key = os.getenv("MINIO_ROOT_PASSWORD", "SecurePass123!")

    return Minio(
        endpoint,
        access_key=access_key,
        secret_key=secret_key,
        secure=False  # False because we are running internally without SSL
    )

def test_connection():
    """Attempts to create a bucket and upload a test file."""
    client = get_minio_client()
    bucket_name = "test-bucket"

    try:
        # 1. Check if bucket exists, create if not
        if not client.bucket_exists(bucket_name):
            client.make_bucket(bucket_name)
            print(f"✅ Success: Bucket '{bucket_name}' created.")
        else:
            print(f"ℹ️ Info: Bucket '{bucket_name}' already exists.")

        # 2. Upload a simple object
        data = b"Hello from Terra Server!"
        client.put_object(
            bucket_name,
            "hello.txt",
            io.BytesIO(data),
            len(data),
            content_type="text/plain"
        )
        print("✅ Success: Test object 'hello.txt' uploaded.")

    except S3Error as err:
        print(f"❌ Error: MinIO operation failed - {err}")
    except Exception as e:
        print(f"❌ Error: Unexpected failure - {e}")

if __name__ == "__main__":
    print("🚀 Starting MinIO Connection Test...")
    test_connection()